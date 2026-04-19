# Chapter 6: 上下文管理

> **Motto**: "上下文终会溢出，你需要一种腾出空间的方法"

> 你的 Agent 现在有 7 个工具、能规划任务、能加载技能。但让它执行一个长任务——读 30 个文件、执行 20 条命令——你会遇到一个新问题：对话消息列表越来越长，直到超过模型的上下文窗口。轻则响应变慢、注意力分散；重则直接报错。本章你将构建一个三层上下文压缩系统，让 Agent 能处理任意长度的任务而不崩溃。

> **Part II 终章**：这是 PLANNING 阶段的最后一章。完成后，你的 Agent 将具备规划、知识和记忆管理三大"思考"能力，为 Part III 的委托机制奠定基础。

![Conceptual: Context compression funnel](images/ch06/fig-06-01-concept.png)

*Figure 6-1. Context compression: distilling a mountain of messages into a dense, essential crystal.*
## The Problem

启动 REPL，给 Agent 一个大任务：

```
You: 帮我审查这个项目的所有 Python 文件。逐个读取，
     找出潜在的 bug 和安全问题，最后写一份报告。
```

Agent 兴致勃勃地开始工作：

```
[Tool: read_file] src/auth.py          → 200 行
[Tool: read_file] src/database.py      → 350 行
[Tool: read_file] src/api/routes.py    → 500 行
[Tool: read_file] src/api/middleware.py → 280 行
...
[Tool: read_file] src/utils/helpers.py  → 150 行
```

读了 15 个文件后，消息列表中已经积累了数千行代码。然后：

```
Error: This request would exceed the model's context window limit.
```

或者更隐蔽的情况——没有报错，但 Agent 开始"失忆"：它忘了前面文件里看到的问题，重复提出相同的建议，或者干脆跳过某些文件。

这不是 Agent 的"智力"问题，而是**物理限制**——上下文窗口有大小上限。

## 6.1 理解上下文窗口

**什么是 Token？**

LLM 不直接处理文字，而是处理 **token**——文本的最小单元。英文中一个 token 大约是 4 个字符（一个常见单词），中文中大约是 1.5 个字符（约半个到一个字）。

```
"Hello, world!"     → ~4 tokens
"你好，世界！"       → ~5 tokens
一行 Python 代码     → ~10-20 tokens
一个 200 行的文件    → ~2,000-4,000 tokens
```

**上下文窗口 = 输入 + 输出的 token 总量**

Claude 的上下文窗口是 200K tokens。听起来很大？让我们算算：

```
System prompt:        ~500 tokens
15 个文件 (平均300行): ~45,000 tokens
15 次 tool_use 消息:   ~3,000 tokens
Agent 的分析文本:      ~5,000 tokens
───────────────────────────────
合计:                  ~53,500 tokens
```

已经用了四分之一。继续工作，很快就会逼近极限。

**更大的窗口不是答案**

你可能想："200K 还不够？那用更大的模型。"问题是：

1. **注意力稀释**：窗口越大，模型对每一段内容的注意力越低。在 200K 窗口中，100K 位置之前的信息检索准确率会显著下降（这就是"大海捞针"问题）。
2. **成本线性增长**：token 按量计费。200K 窗口全部填满的成本是 20K 窗口的 10 倍。
3. **延迟增加**：窗口越大，首次 token 延迟越高。

正确的做法不是"装更多"，而是"及时清理"。

## 6.2 三层压缩策略

我们设计三层渐进式压缩，每层处理不同程度的上下文膨胀：

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

为什么是三层？因为它们处理不同的场景：

- **Layer 1** 是"日常保洁"——大部分时候这就够了。3 轮前读过的文件内容，Agent 早已处理完毕，保留摘要足矣。
- **Layer 2** 是"紧急清理"——当保洁不够用时，整体收缩。代价是丢失所有细节，但至少 Agent 不会崩溃。
- **Layer 3** 是"Agent 的自主判断"——有时候 Agent 比我们更清楚何时该压缩（比如它觉得自己开始重复了）。

## 6.3 实现 context.py

创建 `context.py`——上下文管理的完整实现：

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

**Token 估算**

不需要精确——我们只需要知道"大概快满了没"：

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

为什么不用精确的 tokenizer？因为引入 `tiktoken` 等库增加了依赖，而我们只需要一个"够用"的触发阈值。差 20% 不影响大局。

**Layer 1: 微压缩**

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

关键细节：

1. 只压缩 `tool_result`，不碰 `tool_use`——因为 API 要求 `tool_use` 和 `tool_result` 一一对应，`tool_use` 里的参数通常很短。
2. 检查 `[compacted:` 前缀避免重复压缩。
3. 保留行数和字符数信息——Agent 至少知道"这里曾经有 42 行输出"。

**Layer 2: 自动摘要**

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

注意这里的设计选择：

1. **保存完整记录**：压缩是有损的。保存到 `.transcripts/` 确保不会永久丢失信息。
2. **让 LLM 自己总结**：它最知道哪些信息重要。我们只需要给一个好的提示。
3. **替换后保持 user/assistant 交替**：API 要求消息角色必须交替出现。

**Layer 3: 手动压缩（compact 工具）**

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

工具的 `input_schema` 是空的——不需要任何参数，调用即触发。

**ContextManager 类**

将三层策略统一管理：

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

`on_loop_start` 在每次 LLM 调用前执行——这确保我们永远不会带着超标的上下文去调用 API。

## 6.4 集成到 Agent

改动集中在 `agent_loop` 和 `repl` 两个函数：

**1. 导入**（文件顶部）：

```python
from context import ContextManager, COMPACT_TOOL  # NEW
```

**2. 工具列表**：

```python
TOOLS = [
    # ... 已有的 bash, read_file, write_file, edit_file ...
    TODO_TOOL,
    LOAD_SKILL_TOOL,
    COMPACT_TOOL,  # NEW
]
```

**3. agent_loop 签名和集成**：

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

注意 `compact` handler 用了 `lambda`——因为它不接受参数（tool schema 是空的），但需要访问 `messages` 和 `client`。闭包再次发挥作用。

**4. REPL 更新**：

```python
def repl():
    messages = []
    todo_manager = TodoManager()
    context_manager = ContextManager()  # NEW

    # ... REPL 循环 ...
    agent_loop(messages, todo_manager, context_manager)  # CHANGED
```

## 6.5 试一试

```bash
cd miniagent
python agent.py
```

你应该看到工具列表中多了 `compact`：

```
MiniAgent REPL (输入 'exit' 退出, 'clear' 清空对话)
工作目录: /path/to/miniagent
工具: bash, read_file, write_file, edit_file, todo, load_skill, compact
技能: code-review
--------------------------------------------------
```

测试微压缩——给 Agent 一些需要多轮工具调用的任务：

```
You: 依次读取 agent.py、todo.py、skill_loader.py 和 context.py，
     然后告诉我每个文件的行数。
```

Agent 会用 4 次 `read_file`。观察第 4 次读取时，前面的文件内容会被自动压缩为占位符（因为超过了 3 轮的 `MICRO_COMPACT_AGE`）。

测试手动压缩——在一段长对话后：

```
You: 帮我压缩一下上下文
```

Agent 应该会调用 `compact` 工具，你会看到类似的输出：

```
[Tool: compact] (压缩上下文)
上下文已压缩: 35000 → 800 tokens (节省 34200 tokens)
```

> **Try It Yourself**：修改 `AUTO_COMPACT_THRESHOLD` 为一个很小的值（如 5000），然后观察自动压缩何时触发。感受一下"压缩前"和"压缩后"Agent 记忆的差异。

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

| 指标 | Chapter 5 | Chapter 6 |
|------|-----------|-----------|
| 工具数 | 6 | **7** (+compact) |
| 模块数 | 3 | **4** (+context.py) |
| 能力 | 加载知识 | **+上下文生存** |
| 最大任务长度 | 受限于上下文窗口 | **理论上无限** |

**核心架构演进**：

```
Ch1-3: Agent = Model + 工具
Ch4:   Agent = Model + 工具 + 规划
Ch5:   Agent = Model + 工具 + 规划 + 知识
Ch6:   Agent = Model + 工具 + 规划 + 知识 + 记忆管理  ← you are here
```

**Part II 完成**。你的 Agent 现在不仅能"干活"，还能"思考"：

- **规划**：拆解复杂任务，追踪进度
- **知识**：按需加载领域专业知识
- **记忆**：在有限的上下文窗口中生存，处理任意长任务

这三个能力合在一起，构成了 Agent 的"认知基础设施"。接下来的 Part III，你将在这个基础上让 Agent 学会"委托"——把子任务交给独立的 Agent 处理。

## Summary

- 上下文窗口是有限的物理资源。更大的窗口不是解决方案——注意力稀释、成本增加、延迟变高
- 三层压缩策略渐进应对：微压缩（日常）、自动摘要（紧急）、手动压缩（自主判断）
- 微压缩只替换旧的 `tool_result`，保留结构信息（行数、字符数）
- 自动摘要让 LLM 自己总结对话，保存完整记录到 `.transcripts/` 防止信息永久丢失
- `compact` 工具赋予 Agent 自主判断"何时该压缩"的能力
- 粗略的 token 估算（3 字符/token）足以用于触发阈值——不需要精确 tokenizer

下一章开始 Part III: DELEGATION。你将学会让 Agent 启动子 Agent 来处理子任务——这是从"一个人干活"到"带团队"的跨越。
