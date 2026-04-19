# Chapter 7: 子智能体

> **Motto**: "大任务拆小，每个子任务一个干净的上下文"

> 你的 Agent 现在有 7 个工具，能规划、加载知识、管理上下文。它是一个称职的独立工作者。但给它一个真正复杂的任务——"调研三个竞品的 API，写一份对比报告"——调研过程中读取的大量文件和命令输出会塞满上下文，到写报告时它已经忘了调研的细节。本章你将引入子智能体——独立的 Agent 实例，拥有干净的上下文，完成后只返回精炼的结果。

> **Part III 开始**：从这一章起，你的 Agent 将从"独立工作者"进化为"协调者"。

![Conceptual: Task board with cards in columns](images/ch07/fig-07-01-concept.png)

*Figure 7-1. Sub-agents: delegate tasks to clean, independent workers and collect their results.*
## The Problem

让 Agent 做一个多阶段任务：

```
You: 帮我做以下事情：
     1) 读取 agent.py，分析其代码质量
     2) 读取 context.py，分析其代码质量
     3) 读取 skill_loader.py，分析其代码质量
     4) 综合以上分析，写一份整体审查报告
```

Agent 开始工作。它读取第一个文件（几百行代码进入上下文），分析，再读第二个，分析……到第三个文件时，消息列表已经很长了。虽然第 6 章的微压缩会帮忙清理旧的 tool_result，但分析过程中产生的大量文本——Agent 自己写的分析、读取的代码片段——仍然占据着上下文。

更关键的问题是**注意力分散**。Agent 一边调研一边想着怎么写报告，一边写报告一边回顾调研数据。它的"工作记忆"被各种子任务的细节污染了。

人类处理这种任务的方式是什么？**分工**。让一个人负责调研 agent.py，另一个人调研 context.py，第三个人调研 skill_loader.py，最后由主管综合写报告。每个人只专注于自己的任务，主管只看汇总结果。

## The Solution

引入子智能体（Subagent）——独立的 Agent 实例：

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

关键设计：

1. **干净的上下文**：每个子 Agent 有自己的 `messages = []`，从空白开始。不受父 Agent 已有对话的干扰。
2. **精炼的返回**：子 Agent 完成后，只返回最终的文本回复给父 Agent。中间的工具调用、读取的文件内容、分析过程——全部留在子 Agent 的本地消息列表中，不污染父 Agent。
3. **职责边界**：父 Agent 有 `task` 工具（能委托），子 Agent 没有（防止无限递归）。

## 7.1 实现 subagent.py

创建 `subagent.py`——核心只有一个函数 `run_subagent`：

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

仔细看——这就是一个精简版的 `agent_loop`！同样的 while 循环、同样的工具调度。区别在于：

1. **独立的 `messages`**：`messages = [{"role": "user", "content": prompt}]`，从零开始。
2. **有限的轮次**：`max_turns=20` 防止子 Agent 陷入无限循环。
3. **返回文本**：不是 `print` 给用户，而是 `return` 给父 Agent。

`max_turns` 是一个重要的安全阀。子 Agent 没有人类监督，如果它陷入循环（比如反复读同一个文件），`max_turns` 确保它最终会停下来。

## 7.2 task 工具

子 Agent 需要被父 Agent 调用，所以需要一个工具 schema：

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

`description` 用于日志显示和 todo 追踪。`prompt` 是给子 Agent 的完整指令——**要详细**，因为子 Agent 看不到父 Agent 的对话历史。

## 7.3 集成到 Agent

改动在 `agent.py` 中有三处：

**1. 工具列表分层**：

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

一行列表推导式就完成了工具集的分层。子 Agent 能用所有工具，唯独不能再委托。

**2. Handler 构建**：

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

注意 `child_handlers` 不包含 `todo`、`compact`、`task`——子 Agent 是无状态的一次性执行者，不需要任务管理和上下文压缩。

**3. REPL 输出**——无需改动，因为工具列表已经动态生成，`TASK_TOOL` 自动出现在显示中。

## 7.4 父子 Agent 的职责边界

这个设计中存在一个清晰的职责分工：

| | 父 Agent | 子 Agent |
|---|---|---|
| **角色** | 协调者 | 执行者 |
| **tools** | 8 个 (含 task) | 7 个 (不含 task) |
| **上下文** | 持久，跨多轮 | 临时，用完即弃 |
| **状态** | 有 TodoManager, ContextManager | 无状态 |
| **与用户交互** | 直接对话 | 不与用户交互 |

父 Agent 的最佳使用模式：

1. 收到复杂任务 → 用 `todo` 拆解为步骤
2. 对于可独立完成的步骤 → 用 `task` 委托给子 Agent
3. 对于需要与用户交互的步骤 → 自己处理
4. 汇总子 Agent 的结果 → 生成最终回复

## 7.5 试一试

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

试试委托任务：

```
You: 用子智能体分别分析 agent.py 和 context.py 的代码质量，然后综合写一份报告
```

观察输出——你会看到子 Agent 的缩进日志：

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

关键观察：父 Agent 的消息列表中只有子 Agent 返回的摘要文本，不包含子 Agent 读取的完整文件内容。上下文干净如初。

> **Try It Yourself**：让 Agent 做一个三步任务——"用子智能体分别统计三个文件的行数，然后告诉我哪个最大"。观察父 Agent 如何协调，子 Agent 如何独立执行。

## 7.6 Subagent 模式的局限

子智能体解决了上下文污染的问题，但它有明显的局限：

1. **同步阻塞**：父 Agent 等子 Agent 完成才能继续。如果子任务耗时 30 秒，父 Agent 就卡 30 秒。
2. **一次性的**：子 Agent 完成后就消失了。它不记得上次做过什么。
3. **无状态**：没有自己的 todo、没有上下文压缩。长任务可能超出窗口。
4. **无身份**：你不能说"让上次那个审查员再看一遍"——每次都是全新的。

这些局限都会在后续章节中解决——第 8 章引入后台任务处理同步阻塞，第 9 章引入持久化任务图让子智能体有记忆，第 10 章引入智能体团队给它们身份。

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

| 指标 | Chapter 6 | Chapter 7 |
|------|-----------|-----------|
| 工具数 | 7 | **8** (+task) |
| 模块数 | 4 | **5** (+subagent.py) |
| 能力 | 上下文管理 | **+委托子任务** |
| Agent 角色 | 独立工作者 | **协调者 + 执行者** |

**核心架构演进**：

```
Ch1-3: Agent = Model + 工具
Ch4:   Agent = Model + 工具 + 规划
Ch5-6: Agent = Model + 工具 + 规划 + 知识 + 记忆
Ch7:   Agent = Model + 工具 + 规划 + 知识 + 记忆 + 委托  ← you are here
```

从第 1 章的 30 行到现在，Agent 的 Harness 已经包含了 Agent 系统的大部分核心组件。接下来的两章将继续扩展委托能力——让慢操作能在后台运行，让任务计划能持久化到磁盘。

## Summary

- 复杂任务中，子任务的细节会污染父 Agent 的上下文——注意力分散、记忆混乱
- 子智能体拥有独立的 `messages = []`，从干净的上下文开始，完成后只返回精炼的文本摘要
- `CHILD_TOOLS = [t for t in TOOLS if t["name"] != "task"]`——一行代码实现工具分层，防止递归
- `run_subagent` 本质上是一个精简版的 `agent_loop`——相同的模式，不同的生命周期
- `max_turns` 是子 Agent 的安全阀，防止无限循环
- 父 Agent 是协调者（有 task 工具），子 Agent 是执行者（有执行工具）

下一章，我们将解决子智能体的第一个局限——同步阻塞。当子任务需要运行 `pytest`（2 分钟）或 `npm install`（30 秒）时，父 Agent 不应该傻等。
