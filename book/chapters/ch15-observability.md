# Chapter 15: 可观测性

> **Motto**: "看不见的 Agent 不可信"

> Agent 在"黑箱"中运行。你给它一个任务，它调用了一系列工具，最后给你一个结果。但中间发生了什么？为什么这一步花了 30 秒？为什么 Token 消耗突然翻倍？为什么同一个工具被调用了 5 次？本章添加三个可观测性组件：结构化日志记录每个操作，执行追踪关联整个 Agent 循环，Token 统计跟踪成本。

## The Problem

```
You: 帮我重构 agent.py

Agent: (思考了很久...)
Agent: (调用了很多工具...)
Agent: 重构完成了。

// 但是：
// - 它总共用了多少 Token？花了多少钱？
// - 哪一步最耗时？
// - 为什么调用了 read_file 3 次——是循环了还是确实需要？
// - 如果失败了，在哪一步出的问题？
```

生产环境中，不可观测的系统是不可信的。你无法优化你无法测量的东西，也无法调试你无法追踪的问题。

## 15.1 结构化日志

JSON Lines (JSONL) 格式——每行一条日志记录：

```python
class Logger:
    def __init__(self, log_dir=".logs", filename="agent.jsonl"):
        self._log_path = os.path.join(log_dir, filename)
        os.makedirs(log_dir, exist_ok=True)

    def log(self, level, event, trace_id="", **data):
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "level": level,
            "event": event,
        }
        if trace_id:
            entry["trace_id"] = trace_id
        entry.update(data)
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
```

输出示例：

```json
{"ts": "2025-01-15T10:30:01", "level": "INFO", "event": "llm_call", "trace_id": "a1b2c3d4e5f6", "input_tokens": 2400, "output_tokens": 150, "latency_ms": 1200}
{"ts": "2025-01-15T10:30:02", "level": "INFO", "event": "tool_call", "trace_id": "a1b2c3d4e5f6", "tool": "bash", "latency_ms": 350}
```

为什么用 JSONL 而不是普通文本？
1. **可解析**：每行是有效 JSON，可以用 `jq` 过滤和分析
2. **追加安全**：append-only，不存在写入冲突
3. **结构化查询**：可以按 level、event、trace_id 过滤

便捷方法：

```python
def info(self, event, trace_id="", **data):
    self.log("INFO", event, trace_id, **data)

def llm_call(self, trace_id, input_tokens, output_tokens, latency_ms, stop_reason=""):
    self.info("llm_call", trace_id,
              input_tokens=input_tokens, output_tokens=output_tokens,
              latency_ms=latency_ms, stop_reason=stop_reason)

def tool_call(self, trace_id, tool_name, latency_ms):
    self.info("tool_call", trace_id, tool=tool_name, latency_ms=latency_ms)
```

## 15.2 执行追踪

`Tracer` 为每轮交互生成唯一的 `trace_id`：

```python
class Tracer:
    def __init__(self):
        self.trace_id = ""
        self._spans = []

    def new_trace(self) -> str:
        self.trace_id = uuid.uuid4().hex[:12]
        self._spans = []
        return self.trace_id

    def span(self, name, **attrs) -> dict:
        s = {
            "trace_id": self.trace_id,
            "span_id": uuid.uuid4().hex[:8],
            "name": name,
            "start_ms": round(time.time() * 1000),
            "end_ms": 0,
            **attrs,
        }
        self._spans.append(s)
        return s

    def end_span(self, span_dict):
        span_dict["end_ms"] = round(time.time() * 1000)
```

`trace_id` 贯穿整个 Agent 循环——从接收用户输入到返回结果。所有日志都带上 `trace_id`，就可以追踪一次完整的交互链路。

## 15.3 Token 统计

```python
class TokenStats:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.llm_calls = 0
        self.tool_calls = 0
        self.total_llm_ms = 0
        self.total_tool_ms = 0

    def record(self, input_tokens=0, output_tokens=0, llm_ms=0):
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.llm_calls += 1
        self.total_llm_ms += llm_ms

    def estimated_cost(self) -> float:
        cost_in = self.input_tokens * 3.0 / 1_000_000   # $3/M input
        cost_out = self.output_tokens * 15.0 / 1_000_000 # $15/M output
        return round(cost_in + cost_out, 4)

    def summary(self) -> str:
        return "\n".join([
            f"LLM 调用: {self.llm_calls} 次 ({self.total_llm_ms}ms)",
            f"工具调用: {self.tool_calls} 次 ({self.total_tool_ms}ms)",
            f"Token: {self.input_tokens} in + {self.output_tokens} out",
            f"预估成本: ${self.estimated_cost()}",
        ])
```

价格是近似值——不同模型价格不同。但即使是近似估算，也比完全不知道成本好得多。

## 15.4 ObservabilityManager

整合三个组件：

```python
class ObservabilityManager:
    def __init__(self, log_dir=".logs"):
        self.tracer = Tracer()
        self.stats = TokenStats()
        self.logger = Logger(log_dir=log_dir)

    def start_turn(self) -> str:
        return self.tracer.new_trace()

    def record_llm_call(self, response, latency_ms):
        usage = getattr(response, "usage", None)
        input_t = getattr(usage, "input_tokens", 0) if usage else 0
        output_t = getattr(usage, "output_tokens", 0) if usage else 0
        self.stats.record(input_tokens=input_t, output_tokens=output_t, llm_ms=latency_ms)
        self.logger.llm_call(self.tracer.trace_id, input_t, output_t, latency_ms,
                             getattr(response, "stop_reason", ""))

    def record_tool_call(self, tool_name, latency_ms):
        self.stats.record_tool(tool_ms=latency_ms)
        self.logger.tool_call(self.tracer.trace_id, tool_name, latency_ms)

    def print_summary(self):
        print("\n" + "=" * 40)
        print("  📊 Session 统计")
        print("=" * 40)
        print(self.stats.summary())
        print("=" * 40)
```

## 15.5 集成到 Agent

`agent.py` 的变更集中在 `agent_loop` 和 `repl`：

**agent_loop 增加计时和记录**：

```python
def agent_loop(..., obs=None):
    if obs:
        trace_id = obs.start_turn()
        obs.logger.info("agent_loop_start", trace_id, tools=len(TOOLS))

    while True:
        t0 = time.time()
        response = client.messages.create(...)
        llm_ms = round((time.time() - t0) * 1000)

        if obs:
            obs.record_llm_call(response, llm_ms)

        # ... 在工具执行中 ...
        t1 = time.time()
        output = handler(**block.input)
        tool_ms = round((time.time() - t1) * 1000)
        if obs:
            obs.record_tool_call(block.name, tool_ms)
```

**REPL 增加 stats 命令和退出统计**：

```python
def repl():
    obs = ObservabilityManager()
    print("MiniAgent REPL (输入 'exit' 退出, 'clear' 清空对话, 'stats' 查看统计)")

    # ... 在循环中 ...
    if user_input.lower() == "stats":
        obs.print_summary()
        continue

    # 退出时
    obs.print_summary()
    print("Bye!")
```

## 15.6 调试技巧

有了可观测性，你可以诊断常见问题：

1. **Agent 循环不停**：查看日志中的 `stop_reason`。如果一直是 `tool_use`，Agent 可能陷入了工具调用循环。
2. **Token 消耗暴增**：检查 `input_tokens` 的增长趋势。如果每轮翻倍，可能需要触发 compact。
3. **工具反复调用**：用 `jq '.event' .logs/agent.jsonl | sort | uniq -c | sort -rn` 统计工具调用频率。

## 15.7 试一试

```bash
cd miniagent
python agent.py
```

```
You: 帮我创建一个简单的 Python 函数
...
You: stats
```

你会看到：

```
========================================
  📊 Session 统计
========================================
LLM 调用: 3 次 (4500ms)
工具调用: 2 次 (150ms)
Token: 3200 in + 450 out = 3650 total
预估成本: $0.0163
========================================
```

查看日志文件：

```bash
cat .logs/agent.jsonl | python3 -m json.tool --no-ensure-ascii
```

> **Try It Yourself**：执行一个复杂任务（如"创建并测试一个 Python 项目"），然后用 `stats` 命令看看消耗了多少 Token。用 `jq` 分析日志文件，找出最耗时的工具调用。

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +30 行（import time、obs 参数、LLM/工具计时、stats 命令）
├── observability.py    ← NEW: 204 行（Tracer、TokenStats、Logger、ObservabilityManager）
├── security.py
├── worktree.py
├── autonomous.py
├── protocols.py
├── team.py
├── tasks.py
├── background.py
├── context.py
├── subagent.py
├── skill_loader.py
└── todo.py
```

| 指标 | Chapter 14 | Chapter 15 |
|------|-----------|------------|
| 工具数 | 29 | **29** (工具数不变，增加的是可观测层) |
| 模块数 | 12 | **13** (+observability.py) |
| 能力 | 安全与权限 | **+结构化日志 + 执行追踪 + Token 统计** |
| REPL 命令 | exit, clear | **+stats** |

## Summary

- 不可观测的 Agent 不可信——你无法优化无法测量的东西
- Logger 以 JSONL 格式记录结构化日志，支持按事件类型和 trace_id 过滤
- Tracer 为每轮交互生成唯一 trace_id，贯穿整个调用链
- TokenStats 累计统计 Token 消耗并估算 USD 成本
- ObservabilityManager 整合三个组件，提供简洁的 record/print API
- agent_loop 中用 `time.time()` 计时每次 LLM 调用和工具调用
- REPL 增加 `stats` 命令，退出时自动打印 session 统计
- 日志文件 `.logs/agent.jsonl` 可以用 `jq` 等工具进行离线分析
