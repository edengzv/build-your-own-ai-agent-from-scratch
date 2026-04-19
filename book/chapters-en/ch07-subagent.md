<!-- Translated from: ch07-subagent.md -->

# Chapter 7: Sub-Agents

> **Motto**: "Break big tasks into small ones — one clean context per sub-task."

> Your agent now has 7 tools and can plan, load knowledge, and manage context. It is a competent independent worker. But give it a truly complex task — "research three competitors' APIs and write a comparison report" — and the flood of file contents and command outputs from the research phase fills up the context. By the time it starts writing the report, it has already lost track of the research details. In this chapter you introduce sub-agents — independent agent instances with clean contexts that return only distilled results when they finish.

> **Part III begins**: From this chapter onward, your agent evolves from an "independent worker" into a "coordinator."

![Conceptual: Task board with cards in columns](images/ch07/fig-07-01-concept.png)

*Figure 7-1. Sub-agents: delegate tasks to clean, independent workers and collect their results.*
## The Problem

Have the agent do a multi-stage task:

```
You: 帮我做以下事情：
     1) 读取 agent.py，分析其代码质量
     2) 读取 context.py，分析其代码质量
     3) 读取 skill_loader.py，分析其代码质量
     4) 综合以上分析，写一份整体审查报告
```

The agent gets to work. It reads the first file (a few hundred lines of code enter the context), analyzes it, reads the second, analyzes that... By the third file, the message list is already long. Although Chapter 6's micro-compaction helps clean up old `tool_result` entries, the large volume of text generated during the analysis — the agent's own write-ups, the code snippets it read — still occupies the context.

The more critical problem is **attention fragmentation**. The agent is simultaneously researching and thinking about how to write the report, and simultaneously writing the report and looking back at the research data. Its "working memory" is polluted by the details of various sub-tasks.

How do humans handle this kind of task? **Division of labor.** One person researches agent.py, another researches context.py, a third researches skill_loader.py, and a supervisor synthesizes the final report. Each person focuses only on their own task; the supervisor sees only the summarized results.

## The Solution

Introduce sub-agents — independent agent instances:

```
┌─────────────────────────────────────────────┐
│              父 Agent (Parent)               │
│                                              │
│  messages = [user request, ...]              │
│  tools = [bash, read, write, edit,           │
│           todo, load_skill, compact, task]   │
│                                              │
│  "我需要分析三个文件，让子 Agent 分别处理"   │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ task()   │  │ task()   │  │ task()   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │        │
└───────┼──────────────┼──────────────┼────────┘
        ↓              ↓              ↓
┌──────────────┐┌──────────────┐┌──────────────┐
│  子 Agent 1  ││  子 Agent 2  ││  子 Agent 3  │
│              ││              ││              │
│  messages=[] ││  messages=[] ││  messages=[] │
│  (干净!)     ││  (干净!)     ││  (干净!)     │
│              ││              ││              │
│  分析        ││  分析        ││  分析        │
│  agent.py    ││  context.py  ││  skill_      │
│              ││              ││  loader.py   │
│              ││              ││              │
│  返回: 摘要  ││  返回: 摘要  ││  返回: 摘要  │
└──────────────┘└──────────────┘└──────────────┘
```

Key design decisions:

1. **Clean context**: Each sub-agent has its own `messages = []`, starting from a blank slate. It is not affected by the parent agent's existing conversation.
2. **Distilled returns**: When a sub-agent finishes, it returns only its final text reply to the parent. The intermediate tool calls, file contents it read, and analysis process — all of that stays in the sub-agent's local message list and never pollutes the parent.
3. **Responsibility boundaries**: The parent agent has the `task` tool (can delegate); sub-agents do not (preventing infinite recursion).

## 7.1 Implementing subagent.py

Create `subagent.py` — the core is a single function, `run_subagent`:

```python
def run_subagent(
    description: str,
    prompt: str,
    tools: list,
    tool_handlers: dict,
    system: str,
    model: str = MODEL,
    max_turns: int = 20,
) -> str:
    """启动一个独立的子 Agent，在干净的上下文中执行任务。"""
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": prompt}]  # 干净的起点

    print(f"  [Subagent: {description}] 启动...")

    for turn in range(max_turns):
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=tools,
        )

        messages.append({"role": "assistant", "content": response.content})

        # 完成——提取文本回复
        if response.stop_reason != "tool_use":
            result_parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    result_parts.append(block.text)
            result = "\n".join(result_parts) if result_parts else "(无输出)"
            print(f"  [Subagent: {description}] 完成 (轮次: {turn + 1})")
            return result

        # 执行工具调用
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                handler = tool_handlers.get(block.name)
                if handler is None:
                    output = f"[error: 未知工具 {block.name}]"
                else:
                    print(f"    [Sub-Tool: {block.name}] ...")
                    output = handler(**block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })

        messages.append({"role": "user", "content": tool_results})

    return f"[warning: 达到最大轮次 {max_turns}]"
```

Look carefully — this is just a stripped-down version of `agent_loop`! The same while loop, the same tool dispatch. The differences are:

1. **Independent `messages`**: `messages = [{"role": "user", "content": prompt}]`, starting from zero.
2. **Limited turns**: `max_turns=20` prevents the sub-agent from getting stuck in an infinite loop.
3. **Returns text**: Instead of `print`ing to the user, it `return`s to the parent agent.

`max_turns` is an important safety valve. Sub-agents have no human supervision. If one gets stuck in a loop (say, repeatedly reading the same file), `max_turns` ensures it eventually stops.

## 7.2 The task Tool

The sub-agent needs to be callable by the parent agent, so it needs a tool schema:

```python
TASK_TOOL = {
    "name": "task",
    "description": (
        "将子任务委托给一个独立的子智能体执行。"
        "子智能体拥有独立的上下文，不会污染当前对话。"
        "适用于：调研、分析、生成报告等可独立完成的子任务。"
        "不适用于：需要你亲自确认或与用户交互的操作。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "子任务的简短描述",
            },
            "prompt": {
                "type": "string",
                "description": "交给子智能体的完整任务指令",
            },
        },
        "required": ["description", "prompt"],
    },
}
```

`description` is used for log display and todo tracking. `prompt` is the complete instruction for the sub-agent — **be detailed**, because the sub-agent cannot see the parent agent's conversation history.

## 7.3 Integrating into the Agent

There are three changes in `agent.py`:

**1. Layered tool lists**:

```python
TOOLS = [
    # ... bash, read_file, write_file, edit_file ...
    TODO_TOOL,
    LOAD_SKILL_TOOL,
    COMPACT_TOOL,
    TASK_TOOL,  # NEW: 父 Agent 专属
]

# NEW: 子 Agent 的工具集（不包含 task，防止递归）
CHILD_TOOLS = [t for t in TOOLS if t["name"] != "task"]
```

A single list comprehension handles the tool layering. Sub-agents can use every tool except delegation.

**2. Handler construction**:

```python
def agent_loop(messages, todo_manager=None, context_manager=None):
    client = anthropic.Anthropic()

    handlers = { ... }  # 基础工具 handlers

    # 子 Agent 的 handler 集合（不含 task/todo/compact）
    child_handlers = {
        "bash": handle_bash,
        "read_file": handle_read_file,
        "write_file": handle_write_file,
        "edit_file": handle_edit_file,
        "load_skill": make_load_skill_handler(_skills),
    }

    # task 工具——委托给子 Agent
    def handle_task(description: str, prompt: str) -> str:
        return run_subagent(
            description=description,
            prompt=prompt,
            tools=CHILD_TOOLS,
            tool_handlers=child_handlers,
            system=SYSTEM_TEMPLATE,
        )

    handlers["task"] = handle_task
```

Notice that `child_handlers` does not include `todo`, `compact`, or `task` — sub-agents are stateless, one-shot executors that do not need task management or context compaction.

**3. REPL output** — no changes needed, because the tool list is already generated dynamically and `TASK_TOOL` automatically appears in the display.

## 7.4 Parent-Child Responsibility Boundaries

This design establishes a clear division of responsibilities:

| | Parent Agent | Sub-Agent |
|---|---|---|
| **Role** | Coordinator | Executor |
| **Tools** | 8 (including task) | 7 (excluding task) |
| **Context** | Persistent, spans multiple turns | Temporary, discarded after use |
| **State** | Has TodoManager, ContextManager | Stateless |
| **User interaction** | Talks to the user directly | Does not interact with the user |

The parent agent's optimal usage pattern:

1. Receives a complex task -> uses `todo` to break it into steps
2. For steps that can be completed independently -> uses `task` to delegate to a sub-agent
3. For steps requiring user interaction -> handles them itself
4. Aggregates sub-agent results -> generates the final reply

## 7.5 Try It Out

```bash
cd miniagent
python agent.py
```

```
MiniAgent REPL (输入 'exit' 退出, 'clear' 清空对话)
工作目录: /path/to/miniagent
工具: bash, read_file, write_file, edit_file, todo, load_skill, compact, task
技能: code-review
--------------------------------------------------
```

Try delegating a task:

```
You: 用子智能体分别分析 agent.py 和 context.py 的代码质量，然后综合写一份报告
```

Watch the output — you will see the sub-agent's indented logs:

```
  [Tool: task] 分析 agent.py 代码质量
  [Subagent: 分析 agent.py 代码质量] 启动...
    [Sub-Tool: read_file] agent.py
    [Sub-Tool: load_skill] code-review
  [Subagent: 分析 agent.py 代码质量] 完成 (轮次: 3)
  agent.py 的代码结构清晰...（子 Agent 返回的分析摘要）

  [Tool: task] 分析 context.py 代码质量
  [Subagent: 分析 context.py 代码质量] 启动...
    [Sub-Tool: read_file] context.py
  [Subagent: 分析 context.py 代码质量] 完成 (轮次: 2)
  context.py 使用了三层压缩策略...（子 Agent 返回的分析摘要）

Agent: 综合以上两个子智能体的分析结果...（父 Agent 的综合报告）
```

Key observation: the parent agent's message list contains only the summary text returned by each sub-agent — not the full file contents the sub-agents read. The context stays clean.

> **Try It Yourself**: Have the agent do a three-step task — "Use sub-agents to count the lines in three files separately, then tell me which one is the largest." Observe how the parent agent coordinates and how sub-agents execute independently.

## 7.6 Limitations of the Sub-Agent Pattern

Sub-agents solve the context pollution problem, but they have clear limitations:

1. **Synchronous blocking**: The parent agent waits for the sub-agent to finish before continuing. If a sub-task takes 30 seconds, the parent agent is stuck for 30 seconds.
2. **One-shot**: Once a sub-agent finishes, it is gone. It does not remember what it did last time.
3. **Stateless**: No todo list, no context compaction. Long tasks may exceed the context window.
4. **No identity**: You cannot say "have that same reviewer take another look" — every invocation creates a brand-new agent.

All of these limitations will be addressed in later chapters — Chapter 8 introduces background tasks to handle synchronous blocking, Chapter 9 introduces a persistent task graph to give sub-agents memory, and Chapter 10 introduces agent teams to give them identity.

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +20 行（TASK_TOOL, CHILD_TOOLS, child_handlers, handle_task）
├── todo.py
├── skill_loader.py
├── context.py
├── subagent.py         ← NEW: 125 行（run_subagent, TASK_TOOL, _sub_summarize）
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| Metric | Chapter 6 | Chapter 7 |
|------|-----------|-----------|
| Tool count | 7 | **8** (+task) |
| Module count | 4 | **5** (+subagent.py) |
| Capability | Context management | **+Task delegation** |
| Agent role | Independent worker | **Coordinator + Executor** |

**Core architecture evolution**:

```
Ch1-3: Agent = Model + 工具
Ch4:   Agent = Model + 工具 + 规划
Ch5-6: Agent = Model + 工具 + 规划 + 知识 + 记忆
Ch7:   Agent = Model + 工具 + 规划 + 知识 + 记忆 + 委托  ← you are here
```

From the 30 lines in Chapter 1 to now, the agent's harness already contains most of the core components of an agent system. The next two chapters will continue to expand the delegation capability — letting slow operations run in the background and letting task plans persist to disk.

## Summary

- In complex tasks, sub-task details pollute the parent agent's context — fragmenting attention and muddling memory
- Sub-agents have their own independent `messages = []`, start from a clean context, and return only distilled text summaries when done
- `CHILD_TOOLS = [t for t in TOOLS if t["name"] != "task"]` — one line of code implements tool layering and prevents recursion
- `run_subagent` is essentially a stripped-down `agent_loop` — same pattern, different lifecycle
- `max_turns` is the sub-agent's safety valve, preventing infinite loops
- The parent agent is the coordinator (has the task tool); sub-agents are executors (have the action tools)

In the next chapter, we tackle the sub-agent's first limitation — synchronous blocking. When a sub-task needs to run `pytest` (2 minutes) or `npm install` (30 seconds), the parent agent should not sit there waiting.
