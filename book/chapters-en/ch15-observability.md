<!-- Translated from: ch15-observability.md -->

# Chapter 15: Observability

> **Motto**: "An agent you cannot see into is an agent you cannot trust."

> Your agent now has security safeguards, multi-agent collaboration, and task management. But it is a black box — you have no idea what it is thinking, why it chose that tool, why that step took 30 seconds, or how much it all cost. This chapter adds structured logging, execution tracing, and token usage statistics, making the agent's behavior fully observable.

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

Looks normal. But:
- How many tokens did this conversation consume?
- Why did that pytest run take 30 seconds?
- Why did the agent read utils.py twice?
- If something goes wrong, can you trace back to the exact step?

The answer is: no. Because the agent's "inner workings" were never recorded.

## The Solution

Three observability components:

1. **Structured logging** (Logger): JSON-formatted logs that record every event
2. **Execution tracing** (Tracer): A trace ID that threads through the entire agent loop
3. **Token statistics** (TokenStats): Token consumption and cost for every LLM call

## 15.1 Structured Logging

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

The log format is JSONL — consistent with mailbox formats and event logs. One JSON object per line:

```json
{"timestamp": "2025-01-15 10:30:00", "level": "INFO", "event": "llm_call", "trace_id": "a1b2c3", "model": "claude-sonnet-4-20250514", "input_tokens": 1520, "output_tokens": 340, "duration_ms": 2100}
{"timestamp": "2025-01-15 10:30:02", "level": "INFO", "event": "tool_call", "trace_id": "a1b2c3", "tool_name": "read_file", "duration_ms": 5}
```

Why JSON instead of plain text? Because JSON can be parsed by programs — you can filter with `jq`, analyze with Python, or visualize in Grafana.

## 15.2 Execution Tracing

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

Each `agent_loop` invocation generates a trace_id. All LLM calls and tool calls within the same conversation share this trace_id — you can use it to track "what did this conversation do in total."

If a sub-agent is invoked, it generates its own trace_id and records the parent_trace_id — forming a trace chain:

```
trace: a1b2c3 (Lead Agent)
  └── trace: d4e5f6 (子 Agent, parent=a1b2c3)
```

## 15.3 Token Statistics

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

Token statistics reveal a lot of useful information:
- Input tokens far exceed output? Your context is bloated and needs compression.
- One particular call used an unusually large number of tokens? It probably read a very large file.
- Cost suddenly spikes? The agent may have entered a loop.

## 15.4 Integrating into the Agent

Key changes inside `agent_loop`:

```python
# 计时 LLM 调用
t0 = time.time()
response = client.messages.create(...)
llm_ms = round((time.time() - t0) * 1000)

# 记录统计
if obs:
    obs.record_llm_call(response, llm_ms)
```

Tool calls are timed the same way:

```python
t1 = time.time()
output = handler(**block.input)
tool_ms = round((time.time() - t1) * 1000)
if obs:
    obs.record_tool_call(block.name, tool_ms)
```

The REPL gains a new `stats` command and automatically prints statistics on exit:

```python
if user_input.lower() == "stats":
    obs.print_summary()
    continue
```

## 15.5 Debugging Tips

With observability in place, you can diagnose common problems:

**Agent loop never terminates**: Check the logs for `stop_reason`. If it is always `tool_use`, the agent is continuously calling tools. Look at which tool specifically — it may be repeatedly reading and writing the same file.

**Token count growing fast**: Look at the `input_tokens` trend. If it increases with every call, the context is not being compressed. Check whether `context_manager` is working properly.

**Slow tool calls**: Check `duration_ms`. If a `bash` call took 30 seconds, it probably timed out. Inspect the command content.

**Costs too high**: Check `estimated_cost`. Compare the input/output token ratio — if input far exceeds output, you are paying for a large context while the agent produces only a small amount of output.

Analyze logs with `jq`:

```bash
# 查看所有 LLM 调用的 token 使用
cat .logs/agent.jsonl | jq 'select(.event == "llm_call") | {input_tokens, output_tokens, duration_ms}'

# 查看最慢的工具调用
cat .logs/agent.jsonl | jq 'select(.event == "tool_call") | {tool_name, duration_ms}' | sort_by(.duration_ms)
```

## 15.6 Try It Out

```bash
cd miniagent
python agent.py
```

```
日志: .logs/agent.jsonl
```

After running a few tasks:

```
You: stats

Token 统计:
  LLM 调用次数: 5
  输入 tokens: 12,340
  输出 tokens: 2,100
  总计 tokens: 14,440
  估算成本: $0.0685
```

Check the log file:

```
You: exit

Token 统计:
  ...
Bye!
```

```bash
cat .logs/agent.jsonl | python3 -m json.tool --no-ensure-ascii
```

> **Try It Yourself**: Use the agent to complete a complex task (such as "read all .py files and generate a summary"), then analyze the logs. Which step consumed the most tokens? Which tool was the slowest?

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

| Metric | Chapter 14 | Chapter 15 |
|--------|------------|------------|
| Tools | 24 | **24** (observability adds no tools) |
| Modules | 12 | **13** (+observability.py) |
| Capabilities | Security sandbox | **+ Structured logging + Tracing + Token statistics** |
| New commands | -- | **stats** (view statistics in the REPL) |

Like the security layer, observability is an **infrastructure layer** — it does not add new agent capabilities, but makes existing capabilities visible and controllable.

The next chapter — also the final one — writes no code. Instead, it looks back at the entire MiniAgent system and compares it with real-world agent frameworks.

## Summary

- Structured logs use JSONL format and can be parsed by jq, Python, or Grafana
- A trace ID threads through all operations in a single conversation, supporting trace chains
- TokenStats records tokens and estimated cost for every LLM call
- Both LLM calls and tool calls are timed (duration_ms)
- The REPL gains a `stats` command, and statistics print automatically on exit
- Observability is used for diagnosing: non-terminating loops, token growth, slow tools, excessive costs
- Logs are stored in `.logs/agent.jsonl` and can be analyzed with command-line tools
