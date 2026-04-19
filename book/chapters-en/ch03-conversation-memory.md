<!-- Translated from: ch03-conversation-memory.md -->

# Chapter 3: Conversation Memory

> **Motto**: "An agent without memory is no different from a function call."

> Right now, MiniAgent is a one-shot program — it runs once and forgets everything. In this chapter, you give it multi-turn conversation ability by running it as an interactive REPL that remembers every interaction throughout a session. Along the way, you will look closely at the structure of the message list — the essence of LLM memory.

![Conceptual: Message cards in a flowing timeline](images/ch03/fig-03-01-concept.png)

*Figure 3-1. Conversation memory: a timeline of messages that gives the agent continuity.*
## The Problem

Open your terminal and give the agent two related instructions back to back:

```bash
python miniagent/agent.py "创建一个 config.json，内容是 {\"port\": 8080}"
python miniagent/agent.py "把刚才那个文件的端口改成 3000"
```

The second instruction fails. The agent has no idea what "that file from just now" refers to — because each run is a separate process with a fresh, empty message list.

This is not the agent's fault; it is a problem with our `main()` function. Every time you run `python agent.py`, a brand-new `messages = []` is created, one request is processed, and the process exits.

To let the agent work continuously, we need the message list to persist across multiple turns of conversation.

## The Solution

The solution is surprisingly simple: keep the `messages` list alive across multiple `agent_loop()` calls.

```
┌──────────────────────────────────────┐
│           REPL (交互循环)             │
│                                      │
│  messages = []  ← 整个会话共享       │
│                                      │
│  ┌─── Round 1 ────────────────────┐  │
│  │ User: "创建 config.json"       │  │
│  │ → agent_loop(messages)         │  │
│  │ ← Agent: "已创建"              │  │
│  │ messages: [user, asst, ...]    │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌─── Round 2 ────────────────────┐  │
│  │ User: "把端口改成 3000"         │  │
│  │ → agent_loop(messages)  ← 带历史│  │
│  │ ← Agent: "已修改"              │  │
│  │ messages: [user, asst, ..., user, asst, ...] │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

By round two, `messages` already contains the full history from round one. The LLM sees that it previously created `config.json`, so it naturally knows what "that file" refers to.

## The Message List Is Memory

An LLM has no real "memory." On every API call, it receives the full message list and "thinks" from scratch. Its "memory" comes entirely from the `messages` array you pass in.

This means:

1. **If you don't pass it, it doesn't remember**: If you send an empty messages list every time, the LLM acts as if meeting you for the first time
2. **If you pass it, it remembers everything**: The LLM sees every single message in the list
3. **Longer means more expensive**: The more messages there are, the more tokens each API call consumes

The message list is the agent's short-term memory. This understanding is critical for later chapters — Chapter 6's context compression is all about solving the "messages too long" problem.

## Message Format in Detail

Before implementing the REPL, let us take a closer look at the structure of the `messages` array. This is the most fundamental data structure in agent development.

A complete conversation looks like this in messages:

```python
messages = [
    # 1. 用户发送请求
    {"role": "user", "content": "列出当前目录的文件"},

    # 2. LLM 回复：请求调用工具
    {"role": "assistant", "content": [
        TextBlock(text="让我查看一下当前目录。"),
        ToolUseBlock(id="tool_01", name="bash", input={"command": "ls"}),
    ]},

    # 3. 工具执行结果（以 user 角色传入）
    {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "tool_01", "content": "agent.py\nREADME.md"},
    ]},

    # 4. LLM 看到工具结果，给出最终回答
    {"role": "assistant", "content": [
        TextBlock(text="当前目录有两个文件：agent.py 和 README.md。"),
    ]},
]
```

Note a few key points:

**Strict role alternation**: Messages must strictly alternate user -> assistant -> user -> assistant. Tool results are not words spoken by the user, but they must be sent with `"role": "user"` — this is an API convention.

**Two shapes of content**:
- User messages: `content` is typically a plain string
- Assistant messages: `content` is a list of blocks that can include `TextBlock` (text) and `ToolUseBlock` (tool-call requests)

**tool_use_id is the pairing key**: Each `ToolUseBlock` has a unique id; the corresponding `tool_result` references it via `tool_use_id`. The LLM uses this to match "this result belongs to which tool I requested."

> **Tip**: If you want to debug agent behavior, printing the `messages` list is the most effective method. Every step's input and output is right there.

## Implementing the Interactive REPL

REPL (Read-Eval-Print Loop) is the classic interaction pattern. Our implementation is straightforward:

```python
def repl():  # NEW
    """交互式对话循环。消息列表在整个会话中持续增长。"""
    messages = []
    print("MiniAgent REPL (输入 'exit' 退出, 'clear' 清空对话)")
    print(f"工作目录: {WORKSPACE}")
    print(f"工具: {', '.join(TOOL_HANDLERS.keys())}")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("Bye!")
            break
        if user_input.lower() == "clear":
            messages.clear()
            print("[对话已清空]")
            continue

        messages.append({"role": "user", "content": user_input})
        agent_loop(messages)
```

The core is just these few lines:

1. `messages = []` is created when the REPL starts, shared across the entire session
2. Each user input is appended to `messages`
3. `agent_loop(messages)` is called — note that `agent_loop` appends the assistant's replies and tool results into messages
4. On the next iteration, `messages` already contains the full history

The `clear` command empties messages, essentially giving the agent "amnesia" for a fresh start.

### Updating the Entry Point

```python
def main():
    if len(sys.argv) >= 2:
        # 单次执行模式 (向后兼容)
        user_input = " ".join(sys.argv[1:])
        messages = [{"role": "user", "content": user_input}]
        print(f"You: {user_input}")
        agent_loop(messages)
    else:
        # NEW: 交互模式
        repl()
```

Now `python agent.py` enters interactive mode, while `python agent.py "instruction"` remains single-shot. Backward compatible.

## System Prompt Design

While we are at it, let us improve the system prompt. Chapter 1's SYSTEM was just one line — too bare-bones:

```python
# Chapter 1 & 2
SYSTEM = "你是一个有用的 AI 助手。你可以通过工具与计算机交互来完成任务。"
```

A better version:

```python
# CHANGED: 更完善的系统提示词
SYSTEM = """你是 MiniAgent，一个通用 AI 助手。你可以通过工具与计算机交互来完成任务。

你的能力：
- 执行 bash 命令
- 读取、写入、编辑文件

规则：
- 优先使用专用文件工具（read_file, write_file, edit_file），而非 bash 命令操作文件
- 如果任务不需要工具，直接用文本回答
- 对不确定的事情，先查看再行动
"""
```

What improved:

1. **Named identity**: Giving the agent the name "MiniAgent" helps the LLM maintain role consistency
2. **Explicit capability boundaries**: Listing what it can do implicitly defines what it cannot
3. **Behavioral guidelines**: Preferring dedicated tools and looking before acting — this reduces the LLM's arbitrary behavior

> **Note**: The system prompt is the "constitution" of agent behavior. It is short now because the agent's capabilities are still simple. As we progress, Chapter 5 will introduce a Skill system that loads domain knowledge on demand, rather than cramming all guidance into the system prompt.

## Running It

Start interactive mode:

```bash
python miniagent/agent.py
```

```
MiniAgent REPL (输入 'exit' 退出, 'clear' 清空对话)
工作目录: /Users/you/miniagent
工具: bash, read_file, write_file, edit_file
--------------------------------------------------

You: 创建一个 todo.txt，内容是三件待办事项

  [Tool: write_file] todo.txt
  已写入 todo.txt (45 字符)

Agent: 已创建 todo.txt，包含三件待办事项：
1. 完成项目报告
2. 回复客户邮件
3. 准备周会演示

You: 第二件改成"预约牙医"

  [Tool: edit_file] todo.txt
  已编辑 todo.txt

Agent: 已将第二件待办事项从"回复客户邮件"修改为"预约牙医"。

You: 读取文件确认一下

  [Tool: read_file] todo.txt
  1. 完成项目报告
  2. 预约牙医
  3. 准备周会演示

Agent: 文件内容确认无误，三件待办事项已更新。
```

Notice rounds two and three — the agent knows what "the second item" refers to and what "the file" means (`todo.txt`). All of this information comes from the history stored in messages.

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| Single-shot execution, forgets immediately | Interactive REPL with multi-turn memory |
| Minimal system prompt | System prompt with identity, capabilities, and guidelines |
| Input only via command-line arguments | Command-line arguments (single-shot) + interactive mode (multi-turn) |
| ~200 lines of code | ~240 lines of code |

**Cumulative capability**: Your MiniAgent can now execute bash commands, safely read and write files, and hold continuous conversations in interactive mode. It remembers the full session context and understands references like "that file" or "the one mentioned above."

## Try It Yourself

1. **Verify**: Start the REPL and have a conversation lasting three or more turns. Confirm the agent remembers previous actions. Then type `clear` and ask "what file did you just create?" — the agent should have no recollection.

2. **Extend**: Add a `history` command to the REPL. When the user types `history`, print each message's role and the first 50 characters of its content. This gives you a direct view of the "memory" structure.

3. **Explore**: Start the REPL and have the agent read 10 large files in succession (each a few hundred lines). Observe how the API response time changes. Think about this: why does it get slower as you go? (Hint: the messages list keeps growing, and the entire history is sent with every call. This is exactly the problem Chapter 6 will solve.)

## Summary

- **The message list is memory**: An LLM has no persistent memory; its "memory" is the messages array you pass in
- **REPL mode**: Sharing a single messages list across multiple turns enables context continuity
- **Message format**: Strict user -> assistant alternation; tool results are sent with the user role
- **tool_use_id** pairs tool requests with their results
- **The system prompt** should include: identity, capability boundaries, and behavioral guidelines
- Memory has a cost: the longer the messages, the slower and more expensive each API call. This motivates the context management work ahead

---

# Part II: PLANNING — Teaching the Agent to Think

> You have built an agent that can execute commands, read and write files, and remember conversations. It can handle simple single-step tasks and work continuously within a session.
>
> But try giving it a complex task — "refactor this module, add error handling, update the tests, and run them to confirm" — and it loses its way. It might skip steps, repeat work, or forget the original goal.
>
> In the next three chapters, you will give it three critical abilities: the ability to plan tasks (Chapter 4), the ability to load knowledge on demand (Chapter 5), and the ability to survive within a limited context window (Chapter 6). After Phase 2, your agent will transform from "a tool that gets work done" into "an assistant that thinks."

## Further Reading

- [Anthropic Messages API Reference](https://docs.anthropic.com/en/api/messages) — The complete specification for message format
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat) — Cross-reference: OpenAI's message format
- Park, J.S., et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." *UIST 2023* — A seminal paper exploring agent memory architectures
