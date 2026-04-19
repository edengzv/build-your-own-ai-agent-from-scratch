# Chapter 15: 可观测性

> **Motto**: "看不见的 Agent 不可信"

> 你的 Agent 现在有安全保障、多 Agent 协作、任务管理。但它是一个黑箱——你不知道它在想什么、为什么选择这个工具、为什么这一步花了 30 秒、总共花了多少钱。本章添加结构化日志、执行追踪、Token 使用统计，让 Agent 的行为完全可观测。

![Conceptual: Modular system integration](images/ch15/fig-15-01-concept.png)

*Figure 15-1. Observability: making the agent transparent — every decision visible, every cost tracked.*
## The Problem

```
You: 帮我重构这个模块

Agent: (开始工作...)
  [Tool: read_file] app.py
  [Tool: read_file] utils.py
  [Tool: edit_file] app.py
  [Tool: bash] python -m pytest
  [Tool: edit_file] utils.py
  ...

Agent: 重构完成！
```

看起来正常。但：
- 这次对话花了多少 token？
- 那个 pytest 为什么跑了 30 秒？
- 为什么 Agent 读了 utils.py 两次？
- 如果出了 bug，能回溯到具体哪一步吗？

答案是：不能。因为 Agent 的"内心活动"没有被记录。

## The Solution

三个可观测性组件：

1. **结构化日志** (Logger)：JSON 格式日志，记录每个事件
2. **执行追踪** (Tracer)：Trace ID 贯穿整个 Agent 循环
3. **Token 统计** (TokenStats)：每次 LLM 调用的 token 消耗和成本

## 15.1 结构化日志

```python
class Logger:
    def __init__(self):
        self._log_file = os.path.join(LOGS_DIR, "agent.jsonl")

    def log(self, level, event, trace_id="", **data):
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "event": event,
            "trace_id": trace_id,
            **data,
        }
        with open(self._log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

日志格式是 JSONL——和邮箱、事件日志一致。每行一个 JSON 对象：

```json
{"timestamp": "2025-01-15 10:30:00", "level": "INFO", "event": "llm_call", "trace_id": "a1b2c3", "model": "claude-sonnet-4-20250514", "input_tokens": 1520, "output_tokens": 340, "duration_ms": 2100}
{"timestamp": "2025-01-15 10:30:02", "level": "INFO", "event": "tool_call", "trace_id": "a1b2c3", "tool_name": "read_file", "duration_ms": 5}
```

为什么选 JSON 而不是纯文本？因为 JSON 可以被程序解析——你可以用 `jq` 过滤、用 Python 分析、导入到 Grafana 可视化。

## 15.2 执行追踪

```python
class Tracer:
    def new_trace(self, parent_trace=""):
        self.trace_id = uuid.uuid4().hex[:12]
        self.parent_trace_id = parent_trace
        return self.trace_id

    def span(self, name, **attributes):
        span = {
            "trace_id": self.trace_id,
            "span_id": uuid.uuid4().hex[:8],
            "name": name,
            "start_time": time.time(),
            ...
        }
        return span
```

每次 `agent_loop` 调用生成一个 trace_id。同一次对话中的所有 LLM 调用和工具调用共享这个 trace_id——你可以用它追踪"这次对话总共做了什么"。

如果子 Agent 被调用，它会生成自己的 trace_id 并记录 parent_trace_id——形成追踪链：

```
trace: a1b2c3 (Lead Agent)
  └── trace: d4e5f6 (子 Agent, parent=a1b2c3)
```

## 15.3 Token 统计

```python
class TokenStats:
    def record(self, input_tokens, output_tokens, model=""):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.llm_calls += 1

    def estimated_cost(self, input_price=3.0, output_price=15.0):
        """估算成本（Claude Sonnet 定价 per 1M tokens）。"""
        input_cost = (self.total_input_tokens / 1_000_000) * input_price
        output_cost = (self.total_output_tokens / 1_000_000) * output_price
        return round(input_cost + output_cost, 4)

    def summary(self):
        return f"""Token 统计:
  LLM 调用次数: {self.llm_calls}
  输入 tokens: {self.total_input_tokens:,}
  输出 tokens: {self.total_output_tokens:,}
  估算成本: ${self.estimated_cost()}"""
```

Token 统计揭示了很多有用的信息：
- 输入 token 远大于输出？说明上下文太臃肿，需要压缩
- 某次调用特别多 token？可能读了一个很大的文件
- 成本突然上升？可能 Agent 进入了循环

## 15.4 集成到 Agent

`agent_loop` 中的关键变化：

```python
# 计时 LLM 调用
t0 = time.time()
response = client.messages.create(...)
llm_ms = round((time.time() - t0) * 1000)

# 记录统计
if obs:
    obs.record_llm_call(response, llm_ms)
```

工具调用同样计时：

```python
t1 = time.time()
output = handler(**block.input)
tool_ms = round((time.time() - t1) * 1000)
if obs:
    obs.record_tool_call(block.name, tool_ms)
```

REPL 新增 `stats` 命令和退出时自动打印统计：

```python
if user_input.lower() == "stats":
    obs.print_summary()
    continue
```

## 15.5 调试技巧

有了可观测性，你可以诊断常见问题：

**Agent 循环不终止**：查看日志中 `stop_reason`，如果一直是 `tool_use`，说明 Agent 在持续调用工具。查看具体是哪个工具——可能在重复读写同一个文件。

**Token 快速增长**：查看 `input_tokens` 趋势。如果每次调用都在增长，说明上下文没有被压缩。检查 `context_manager` 是否正常工作。

**工具调用缓慢**：查看 `duration_ms`。如果某个 `bash` 调用花了 30 秒，可能是超时了。检查命令内容。

**成本过高**：查看 `estimated_cost`。对比输入/输出 token 比例——如果输入远大于输出，说明你在为大量上下文付费但 Agent 只产生少量输出。

用 `jq` 分析日志：

```bash
# 查看所有 LLM 调用的 token 使用
cat .logs/agent.jsonl | jq 'select(.event == "llm_call") | {input_tokens, output_tokens, duration_ms}'

# 查看最慢的工具调用
cat .logs/agent.jsonl | jq 'select(.event == "tool_call") | {tool_name, duration_ms}' | sort_by(.duration_ms)
```

## 15.6 试一试

```bash
cd miniagent
python agent.py
```

```
日志: .logs/agent.jsonl
```

执行几个任务后：

```
You: stats

Token 统计:
  LLM 调用次数: 5
  输入 tokens: 12,340
  输出 tokens: 2,100
  总计 tokens: 14,440
  估算成本: $0.0685
```

查看日志文件：

```
You: exit

Token 统计:
  ...
Bye!
```

```bash
cat .logs/agent.jsonl | python3 -m json.tool --no-ensure-ascii
```

> **Try It Yourself**：用 Agent 完成一个复杂任务（如"读取所有 .py 文件并生成摘要"），然后分析日志。哪个步骤最耗 token？哪个工具最慢？

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +30 行（计时、记录、stats 命令）
├── todo.py
├── skill_loader.py
├── context.py
├── subagent.py
├── background.py
├── tasks.py
├── team.py
├── protocols.py
├── autonomous.py
├── worktree.py
├── security.py
├── observability.py    ← NEW: 204 行（Tracer、TokenStats、Logger、ObservabilityManager）
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| 指标 | Chapter 14 | Chapter 15 |
|------|------------|------------|
| 工具数 | 24 | **24**（可观测性不增加工具）|
| 模块数 | 12 | **13** (+observability.py) |
| 能力 | 安全沙箱 | **+结构化日志 + 追踪 + Token 统计** |
| 新命令 | — | **stats**（REPL 中查看统计）|

和安全层一样，可观测性是一个**基础设施层**——不增加新的 Agent 功能，而是让现有功能变得可见和可控。

下一章——也是最后一章——不写代码，而是回顾整个 MiniAgent 系统，并与真实世界的 Agent 框架对比。

## Summary

- 结构化日志用 JSONL 格式记录，可被 jq/Python/Grafana 解析
- Trace ID 贯穿一次对话的所有操作，支持追踪链
- TokenStats 记录每次 LLM 调用的 token 和估算成本
- LLM 调用和工具调用都有计时（duration_ms）
- REPL 新增 `stats` 命令，退出时自动打印统计
- 可观测性用于诊断：循环不终止、token 增长、工具缓慢、成本过高
- 日志存储在 `.logs/agent.jsonl`，可用命令行工具分析
