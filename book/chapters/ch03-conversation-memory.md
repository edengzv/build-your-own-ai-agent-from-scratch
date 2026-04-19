# Chapter 3: 对话记忆

> **Motto**: "没有记忆的 Agent 和函数调用没有区别"

> 目前的 MiniAgent 每次运行都是一次性的——执行完就忘记一切。本章你将让它拥有多轮对话能力，以交互式 REPL 运行，记住整个会话中的所有交互。同时，你将深入理解消息列表的结构——这是 LLM 记忆的本质。

![Conceptual: Message cards in a flowing timeline](images/ch03/fig-03-01-concept.png)

*Figure 3-1. Conversation memory: a timeline of messages that gives the agent continuity.*
## The Problem

打开终端，连续给 Agent 两个相关的指令：

```bash
python miniagent/agent.py "创建一个 config.json，内容是 {\"port\": 8080}"
python miniagent/agent.py "把刚才那个文件的端口改成 3000"
```

第二条指令会失败。Agent 不知道"刚才那个文件"是什么——因为每次运行都是一个独立的进程，消息列表从空开始。

这不是 Agent 的问题，是我们的 `main()` 函数的问题。每次 `python agent.py` 都创建一个全新的 `messages = []`，然后执行一次就退出。

想让 Agent 能连续工作，我们需要让消息列表在多轮对话中持续存在。

## The Solution

解决方案出奇地简单：让 `messages` 列表在多次 `agent_loop()` 调用之间保持不变。

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

第二轮时，`messages` 里已经有了第一轮的全部历史。LLM 看到它自己曾经创建了 `config.json`，自然知道"刚才那个文件"是什么。

## 消息列表就是记忆

LLM 没有真正的"记忆"。每次 API 调用，它收到的是完整的消息列表，然后从零开始"思考"。它的"记忆"完全来自于你传给它的 `messages` 数组。

这意味着：

1. **不传就不记得**：如果你每次都传空的 messages，LLM 永远像第一次见面
2. **传了就全记得**：messages 里的每一条消息，LLM 都会看到
3. **越长越贵**：消息越多，每次 API 调用消耗的 token 越多

消息列表就是 Agent 的短期记忆。这个理解对后续章节至关重要——Chapter 6 的上下文压缩就是在解决"消息太长"的问题。

## 消息格式详解

在实现 REPL 之前，让我们深入了解 `messages` 数组的结构。这是 Agent 开发中最基础的数据结构。

一个完整的对话在 messages 中是这样的：

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

注意几个关键点：

**角色交替**：消息严格按 user → assistant → user → assistant 交替。工具结果虽然不是用户说的话，但必须用 `"role": "user"` 传入——这是 API 的约定。

**content 的两种形态**：
- 用户消息：`content` 通常是纯字符串
- assistant 消息：`content` 是一个块列表，可以包含 `TextBlock`（文字）和 `ToolUseBlock`（工具调用请求）

**tool_use_id 是配对的钥匙**：每个 `ToolUseBlock` 有唯一 id，对应的 `tool_result` 通过 `tool_use_id` 关联。LLM 用它来匹配"这个结果是我请求的哪个工具的"。

> **Tip**: 如果你想调试 Agent 的行为，打印 `messages` 列表是最有效的方法。每一步的输入输出都在里面。

## 实现交互式 REPL

REPL（Read-Eval-Print Loop）是最经典的交互模式。我们的实现非常直接：

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

核心就是这几行：

1. `messages = []` 在 REPL 开始时创建，整个会话共享
2. 每次用户输入，追加到 `messages`
3. 调用 `agent_loop(messages)`——注意 `agent_loop` 会在 messages 里追加 assistant 回复和工具结果
4. 下一轮循环时，`messages` 已经包含了全部历史

`clear` 命令清空 messages，等于让 Agent "失忆"重新开始。

### 更新入口函数

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

现在 `python agent.py` 进入交互模式，`python agent.py "指令"` 仍然是单次执行。向后兼容。

## 系统提示词设计

趁着这一章，让我们改进系统提示词。Chapter 1 的 SYSTEM 只有一句话，太简陋了：

```python
# Chapter 1 & 2
SYSTEM = "你是一个有用的 AI 助手。你可以通过工具与计算机交互来完成任务。"
```

更好的版本：

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

改进了什么：

1. **命名身份**：给 Agent 一个名字"MiniAgent"。这帮助 LLM 保持角色一致性
2. **明确能力边界**：列出能做什么，隐含了不能做什么
3. **行为规范**：优先用专用工具、不确定时先查看——这减少了 LLM 的随意行为

> **Note**: 系统提示词是 Agent 行为的"宪法"。现在它很短，因为 Agent 的能力还很简单。随着章节推进，我们会在 Chapter 5 引入 Skill 系统来按需加载领域知识，而不是把所有指导塞进 system prompt。

## 运行效果

启动交互模式：

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

注意第二轮和第三轮——Agent 知道"第二件"指的是什么，知道"文件"指的是 `todo.txt`。这些信息全部来自 messages 中的历史记录。

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 单次执行，用完即忘 | 交互式 REPL，多轮记忆 |
| 极简的系统提示词 | 有身份、能力、规范的提示词 |
| 只能通过命令行参数输入 | 命令行参数 (单次) + 交互模式 (多轮) |
| ~200 行代码 | ~240 行代码 |

**Cumulative capability**: 你的 MiniAgent 现在能执行 bash 命令、安全地读写文件、以交互模式连续对话。它记住整个会话的上下文，能理解"那个文件""上面提到的"这类指代。

## Try It Yourself

1. **Verify**: 启动 REPL，进行一段三轮以上的对话，确认 Agent 能记住之前的操作。然后输入 `clear`，再问"刚才创建了什么文件"——Agent 应该不记得了。

2. **Extend**: 在 REPL 中添加一个 `history` 命令，输入 `history` 时打印当前 `messages` 列表中的每条消息的 role 和前 50 个字符。这能帮你直观地看到"记忆"的结构。

3. **Explore**: 启动 REPL，连续让 Agent 读取 10 个大文件（每个几百行）。观察 API 调用的响应时间变化。思考：为什么越到后面越慢？（提示：messages 列表越来越长，每次都要发送全部历史。这就是 Chapter 6 要解决的问题。）

## Summary

- **消息列表就是记忆**：LLM 没有持久记忆，它的"记忆"就是你传给它的 messages 数组
- **REPL 模式**：在多轮对话中共享同一个 messages 列表，实现上下文保持
- **消息格式**：严格的 user → assistant 交替，工具结果以 user 角色传入
- **tool_use_id** 将工具请求和结果配对
- **系统提示词**应该包含：身份、能力边界、行为规范
- 记忆是有代价的：消息越长，API 调用越慢、越贵。这是后续上下文管理的动机

---

# Part II: PLANNING — 让 Agent 会思考

> 你已经构建了一个能执行命令、读写文件、记住对话的 Agent。它能处理简单的单步任务，也能在一次会话中连续工作。
>
> 但试试给它一个复杂任务——"重构这个模块，添加错误处理，更新测试，最后运行确认"——它会迷失方向。它可能跳过步骤、重复工作、或者忘记最初的目标。
>
> 接下来三章，你将赋予它三种关键能力：规划任务的能力（Chapter 4）、按需加载知识的能力（Chapter 5）、以及在有限上下文窗口中生存的能力（Chapter 6）。完成 Phase 2 后，你的 Agent 将从一个"能干活的工具"变成"会思考的助手"。

## Further Reading

- [Anthropic Messages API Reference](https://docs.anthropic.com/en/api/messages) — 消息格式的完整规范
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat) — 对比参考：OpenAI 的消息格式
- Park, J.S., et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." *UIST 2023* — 探讨 Agent 记忆架构的经典论文
