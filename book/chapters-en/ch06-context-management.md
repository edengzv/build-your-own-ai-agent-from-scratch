<!-- Translated from: ch06-context-management.md -->

# Chapter 6: Context Management

> **Motto**: "Context will overflow eventually — you need a way to make room."

> Your agent now has 7 tools, can plan tasks, and can load skills. But give it a long task — read 30 files, execute 20 commands — and you hit a new problem: the conversation message list grows and grows until it exceeds the model's context window. In mild cases, responses slow down and attention drifts; in severe cases, you get a hard error. In this chapter you build a three-layer context compression system that lets the agent handle tasks of arbitrary length without crashing.

> **Part II Finale**: This is the last chapter of the PLANNING phase. When you finish, your agent will have three "thinking" capabilities — planning, knowledge, and memory management — laying the foundation for Part III's delegation mechanisms.

![Conceptual: Context compression funnel](images/ch06/fig-06-01-concept.png)

*Figure 6-1. Context compression: distilling a mountain of messages into a dense, essential crystal.*
## The Problem

Fire up the REPL and give the agent a big task:

```
You: 帮我审查这个项目的所有 Python 文件。逐个读取，
     找出潜在的 bug 和安全问题，最后写一份报告。
```

The agent eagerly starts working:

```
[Tool: read_file] src/auth.py          → 200 行
[Tool: read_file] src/database.py      → 350 行
[Tool: read_file] src/api/routes.py    → 500 行
[Tool: read_file] src/api/middleware.py → 280 行
...
[Tool: read_file] src/utils/helpers.py  → 150 行
```

After reading 15 files, thousands of lines of code have accumulated in the message list. Then:

```
Error: This request would exceed the model's context window limit.
```

Or something more insidious — no error, but the agent starts "losing its memory": it forgets issues it spotted in earlier files, repeats the same suggestions, or simply skips files altogether.

This is not a problem with the agent's "intelligence" — it is a **physical limitation**. The context window has a hard size limit.

## 6.1 Understanding the Context Window

**What is a token?**

LLMs do not process text directly — they process **tokens**, the smallest units of text. In English, one token is roughly 4 characters (one common word). In Chinese, one token is roughly 1.5 characters (about half to one character).

```
"Hello, world!"     → ~4 tokens
"你好，世界！"       → ~5 tokens
一行 Python 代码     → ~10-20 tokens
一个 200 行的文件    → ~2,000-4,000 tokens
```

**Context window = total tokens for input + output**

Claude's context window is 200K tokens. Sounds huge? Let us do the math:

```
System prompt:        ~500 tokens
15 个文件 (平均300行): ~45,000 tokens
15 次 tool_use 消息:   ~3,000 tokens
Agent 的分析文本:      ~5,000 tokens
───────────────────────────────
合计:                  ~53,500 tokens
```

That is already a quarter used up. Keep working, and you will hit the limit soon.

**A bigger window is not the answer**

You might think: "200K is not enough? Just use a bigger model." The problem is:

1. **Attention dilution**: The bigger the window, the less attention the model pays to each piece of content. In a 200K window, retrieval accuracy for information before the 100K mark drops significantly (this is the "needle in a haystack" problem).
2. **Linear cost growth**: Tokens are billed by volume. Filling a 200K window costs 10x more than a 20K window.
3. **Increased latency**: The bigger the window, the higher the time-to-first-token latency.

The right approach is not "stuff more in" — it is "clean up promptly."

## 6.2 Three-Layer Compression Strategy

We design three progressive compression layers, each handling a different degree of context bloat:

```
┌─────────────────────────────────────────────────┐
│  Layer 1: 微压缩 (micro_compact)                 │
│  每轮自动执行                                     │
│  将 3 轮前的 tool_result 替换为占位符              │
│  "[compacted: 42 lines, 1200 chars]"             │
│  节省: 温和 (保留结构，丢弃细节)                   │
├─────────────────────────────────────────────────┤
│  Layer 2: 自动摘要 (auto_compact)                │
│  当 token 估算超过 50K 时触发                     │
│  LLM 生成对话摘要，替换所有消息                    │
│  完整记录保存到 .transcripts/                     │
│  节省: 激进 (只保留摘要)                          │
├─────────────────────────────────────────────────┤
│  Layer 3: 手动压缩 (compact tool)                │
│  Agent 主动调用                                   │
│  等同于 Layer 2，但由 Agent 判断时机               │
│  用于 Agent 察觉"我快忘了"的情况                  │
└─────────────────────────────────────────────────┘
```

Why three layers? Because they handle different scenarios:

- **Layer 1** is "daily housekeeping" — most of the time this is all you need. The contents of a file read 3 rounds ago have already been processed; keeping a summary placeholder is enough.
- **Layer 2** is "emergency cleanup" — when housekeeping is not sufficient, shrink everything. The cost is losing all details, but at least the agent does not crash.
- **Layer 3** is "the agent's own judgment" — sometimes the agent knows better than we do when to compress (for example, when it senses it is starting to repeat itself).

## 6.3 Implementing context.py

Create `context.py` — the complete implementation of context management:

```python
"""
MiniAgent — Context Manager
三层上下文压缩策略，让 Agent 能处理任意长度的任务。
"""

import os
import json
import time

# 简单的 token 估算：取中间值，约 3 字符/token
TOKEN_CHAR_RATIO = 3
AUTO_COMPACT_THRESHOLD = 50000  # tokens
MICRO_COMPACT_AGE = 3  # 超过 N 轮的 tool_result 会被压缩
TRANSCRIPTS_DIR = os.path.join(os.getcwd(), ".transcripts")
```

**Token estimation**

No need for precision — we just need to know "are we roughly close to full yet":

```python
def estimate_tokens(messages: list) -> int:
    """粗略估算消息列表的 token 数。"""
    total_chars = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for block in content:
                total_chars += len(str(block))
    return total_chars // TOKEN_CHAR_RATIO
```

Why not use a precise tokenizer? Because importing `tiktoken` or similar libraries adds a dependency, and all we need is a "good enough" trigger threshold. Being off by 20% does not change the outcome.

**Layer 1: Micro-compaction**

```python
def micro_compact(messages: list, current_round: int) -> int:
    """将旧的 tool_result 替换为摘要占位符。返回压缩数量。"""
    compacted = 0
    round_counter = 0

    for i, msg in enumerate(messages):
        if msg["role"] == "user" and isinstance(msg.get("content"), list):
            round_counter += 1
            age = current_round - round_counter

            if age >= MICRO_COMPACT_AGE:
                for j, block in enumerate(msg["content"]):
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        content = block.get("content", "")
                        if isinstance(content, str) and not content.startswith("[compacted:"):
                            lines = content.count("\n") + 1
                            chars = len(content)
                            block["content"] = f"[compacted: {lines} lines, {chars} chars]"
                            compacted += 1
    return compacted
```

Key details:

1. Only `tool_result` gets compacted, never `tool_use` — because the API requires a one-to-one correspondence between `tool_use` and `tool_result`, and the parameters inside `tool_use` are usually short.
2. The `[compacted:` prefix check prevents double-compaction.
3. Line count and character count are preserved — the agent at least knows "there used to be 42 lines of output here."

**Layer 2: Auto-summary**

```python
def auto_compact(messages: list, client) -> list:
    """让 LLM 自己总结对话，用摘要替换所有消息。"""
    # 保存完整记录
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    transcript_file = os.path.join(
        TRANSCRIPTS_DIR, f"transcript_{int(time.time())}.json"
    )
    # ... 序列化并保存 ...

    # 让 LLM 总结
    summary_prompt = (
        "请总结以上对话的关键信息，包括：\n"
        "1. 用户的原始任务目标\n"
        "2. 已完成的步骤和结果\n"
        "3. 当前进行中的任务\n"
        "4. 任何需要记住的重要上下文\n"
        "用 200 字以内总结。"
    )

    summary_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=messages + [{"role": "user", "content": summary_prompt}],
    )

    # 用摘要替换所有消息
    new_messages = [
        {
            "role": "user",
            "content": f"[上下文压缩] 以下是之前对话的摘要:\n\n{summary_text}\n\n"
                       f"完整记录已保存到: {transcript_file}\n"
                       "请基于这个摘要继续工作。",
        },
        {
            "role": "assistant",
            "content": "好的，我已了解之前的对话内容。请继续。",
        },
    ]
    return new_messages
```

Note the design choices here:

1. **Save the full transcript**: Compression is lossy. Saving to `.transcripts/` ensures no information is permanently lost.
2. **Let the LLM summarize itself**: It knows best which information matters. We just need to give it a good prompt.
3. **Maintain user/assistant alternation after replacement**: The API requires message roles to alternate.

**Layer 3: Manual compaction (the compact tool)**

```python
COMPACT_TOOL = {
    "name": "compact",
    "description": (
        "压缩当前对话上下文。当对话变得很长、响应变慢时使用。"
        "会生成对话摘要，丢弃详细历史，保留关键信息。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}
```

The tool's `input_schema` is empty — no parameters needed; calling it is the trigger.

**The ContextManager class**

Unify all three layers under one manager:

```python
class ContextManager:
    """管理上下文压缩的三层策略。"""

    def __init__(self):
        self.round_counter = 0

    def on_loop_start(self, messages: list, client) -> None:
        """每轮 agent_loop 开始时调用。"""
        self.round_counter += 1

        # Layer 1: 微压缩
        micro_compact(messages, self.round_counter)

        # Layer 2: 自动压缩
        tokens = estimate_tokens(messages)
        if tokens > AUTO_COMPACT_THRESHOLD:
            print(f"  [Context] 自动压缩: {tokens} tokens 超过阈值")
            new_messages = auto_compact(messages, client)
            messages.clear()
            messages.extend(new_messages)

    def handle_compact(self, messages: list, client) -> str:
        """Layer 3: 手动压缩的 handler。"""
        return manual_compact(messages, client)
```

`on_loop_start` runs before every LLM call — this ensures we never send an over-budget context to the API.

## 6.4 Integrating into the Agent

The changes are concentrated in the `agent_loop` and `repl` functions:

**1. Import** (top of file):

```python
from context import ContextManager, COMPACT_TOOL  # NEW
```

**2. Tool list**:

```python
TOOLS = [
    # ... 已有的 bash, read_file, write_file, edit_file ...
    TODO_TOOL,
    LOAD_SKILL_TOOL,
    COMPACT_TOOL,  # NEW
]
```

**3. agent_loop signature and integration**:

```python
def agent_loop(
    messages: list,
    todo_manager: TodoManager | None = None,
    context_manager: ContextManager | None = None,  # NEW
) -> None:
    client = anthropic.Anthropic()

    handlers = { ... }
    # NEW: compact 工具需要 messages 和 client
    if context_manager is not None:
        handlers["compact"] = lambda: context_manager.handle_compact(messages, client)

    while True:
        # ... 提醒注入 ...

        # NEW: 上下文压缩（每轮自动执行）
        if context_manager is not None:
            context_manager.on_loop_start(messages, client)

        response = client.messages.create(...)
        # ... 其余不变 ...
```

Notice the `compact` handler uses a `lambda` — because it takes no parameters (the tool schema is empty), but it needs access to `messages` and `client`. Closures come to the rescue once again.

**4. REPL update**:

```python
def repl():
    messages = []
    todo_manager = TodoManager()
    context_manager = ContextManager()  # NEW

    # ... REPL 循环 ...
    agent_loop(messages, todo_manager, context_manager)  # CHANGED
```

## 6.5 Try It Out

```bash
cd miniagent
python agent.py
```

You should see `compact` in the tool list:

```
MiniAgent REPL (输入 'exit' 退出, 'clear' 清空对话)
工作目录: /path/to/miniagent
工具: bash, read_file, write_file, edit_file, todo, load_skill, compact
技能: code-review
--------------------------------------------------
```

Test micro-compaction — give the agent a task that requires multiple rounds of tool calls:

```
You: 依次读取 agent.py、todo.py、skill_loader.py 和 context.py，
     然后告诉我每个文件的行数。
```

The agent will use `read_file` four times. Watch how on the 4th read, the contents of earlier files get automatically compacted to placeholders (because they exceed the 3-round `MICRO_COMPACT_AGE`).

Test manual compaction — after a long conversation:

```
You: 帮我压缩一下上下文
```

The agent should call the `compact` tool, and you will see output like this:

```
[Tool: compact] (压缩上下文)
上下文已压缩: 35000 → 800 tokens (节省 34200 tokens)
```

> **Try It Yourself**: Set `AUTO_COMPACT_THRESHOLD` to a very small value (say 5000), then observe when auto-compaction triggers. Feel the difference in the agent's memory "before compression" versus "after compression."

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +25 行（context_manager 参数、compact handler、on_loop_start 调用）
├── todo.py
├── skill_loader.py
├── context.py          ← NEW: 188 行（三层压缩、ContextManager、COMPACT_TOOL）
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| Metric | Chapter 5 | Chapter 6 |
|--------|-----------|-----------|
| Tools | 6 | **7** (+compact) |
| Modules | 3 | **4** (+context.py) |
| Capability | Load knowledge | **+context survival** |
| Max task length | Limited by context window | **Theoretically unlimited** |

**Core architecture evolution**:

```
Ch1-3: Agent = Model + 工具
Ch4:   Agent = Model + 工具 + 规划
Ch5:   Agent = Model + 工具 + 规划 + 知识
Ch6:   Agent = Model + 工具 + 规划 + 知识 + 记忆管理  ← you are here
```

**Part II complete.** Your agent can now not only "do work" but also "think about work":

- **Planning**: Break complex tasks into steps, track progress
- **Knowledge**: Load domain expertise on demand
- **Memory**: Survive within a finite context window, handle tasks of any length

These three capabilities together form the agent's "cognitive infrastructure." In the upcoming Part III, you will build on this foundation and teach the agent to "delegate" — hand off subtasks to independent agents.

## Summary

- The context window is a finite physical resource. A bigger window is not the solution — attention dilutes, costs rise, latency increases
- A three-layer compression strategy handles this progressively: micro-compaction (routine), auto-summary (emergency), manual compaction (autonomous judgment)
- Micro-compaction only replaces old `tool_result` content, preserving structural information (line count, character count)
- Auto-summary lets the LLM summarize the conversation itself, saving the full transcript to `.transcripts/` to prevent permanent information loss
- The `compact` tool gives the agent the ability to autonomously judge "when to compress"
- A rough token estimate (3 characters/token) is sufficient for trigger thresholds — no precise tokenizer needed

The next chapter begins Part III: DELEGATION. You will learn how to have the agent launch sub-agents to handle subtasks — the leap from "one person doing the work" to "leading a team."
