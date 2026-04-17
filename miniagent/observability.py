"""
observability — 可观测性模块

提供结构化日志、执行追踪和 Token 统计。

核心组件：
- Tracer: 为每轮对话生成 trace_id，追踪 span
- TokenStats: 累计统计 Token 消耗和预估成本
- Logger: 结构化 JSONL 日志，写入 .logs/agent.jsonl
- ObservabilityManager: 整合以上组件的便捷接口

用法：
    obs = ObservabilityManager()
    trace_id = obs.start_turn()
    obs.record_llm_call(response, latency_ms=1200)
    obs.record_tool_call("bash", latency_ms=350)
    obs.print_summary()
"""

import json
import os
import time
import uuid


# ── Tracer ───────────────────────────────────────────────────

class Tracer:
    """为每轮交互生成唯一 trace_id，支持嵌套 span。"""

    def __init__(self):
        self.trace_id: str = ""
        self._spans: list[dict] = []

    def new_trace(self) -> str:
        """开始新的 trace，返回 trace_id。"""
        self.trace_id = uuid.uuid4().hex[:12]
        self._spans = []
        return self.trace_id

    def span(self, name: str, **attrs) -> dict:
        """记录一个 span（工具调用、LLM 调用等）。"""
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

    def end_span(self, span_dict: dict) -> None:
        """结束一个 span，记录结束时间。"""
        span_dict["end_ms"] = round(time.time() * 1000)

    @property
    def spans(self) -> list[dict]:
        return list(self._spans)


# ── TokenStats ───────────────────────────────────────────────

# 近似价格（每百万 token，USD）
_PRICE_INPUT = 3.0
_PRICE_OUTPUT = 15.0


class TokenStats:
    """累计统计 Token 消耗。"""

    def __init__(self):
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.llm_calls: int = 0
        self.tool_calls: int = 0
        self.total_llm_ms: int = 0
        self.total_tool_ms: int = 0

    def record(self, input_tokens: int = 0, output_tokens: int = 0,
               llm_ms: int = 0) -> None:
        """记录一次 LLM 调用的 token 消耗。"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.llm_calls += 1
        self.total_llm_ms += llm_ms

    def record_tool(self, tool_ms: int = 0) -> None:
        """记录一次工具调用。"""
        self.tool_calls += 1
        self.total_tool_ms += tool_ms

    def estimated_cost(self) -> float:
        """估算 USD 成本。"""
        cost_in = self.input_tokens * _PRICE_INPUT / 1_000_000
        cost_out = self.output_tokens * _PRICE_OUTPUT / 1_000_000
        return round(cost_in + cost_out, 4)

    def summary(self) -> str:
        """返回人类可读的统计摘要。"""
        lines = [
            f"LLM 调用: {self.llm_calls} 次 ({self.total_llm_ms}ms)",
            f"工具调用: {self.tool_calls} 次 ({self.total_tool_ms}ms)",
            f"Token: {self.input_tokens} in + {self.output_tokens} out = {self.input_tokens + self.output_tokens} total",
            f"预估成本: ${self.estimated_cost()}",
        ]
        return "\n".join(lines)


# ── Logger ───────────────────────────────────────────────────

class Logger:
    """结构化 JSONL 日志。

    每条日志是一个 JSON 对象，写入 .logs/agent.jsonl。
    """

    def __init__(self, log_dir: str = ".logs", filename: str = "agent.jsonl"):
        self._log_dir = log_dir
        self._log_path = os.path.join(log_dir, filename)
        os.makedirs(log_dir, exist_ok=True)

    def log(self, level: str, event: str, trace_id: str = "",
            **data) -> None:
        """写一条结构化日志。"""
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "level": level,
            "event": event,
        }
        if trace_id:
            entry["trace_id"] = trace_id
        entry.update(data)
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass  # 日志写入失败不应中断主流程

    def info(self, event: str, trace_id: str = "", **data) -> None:
        self.log("INFO", event, trace_id, **data)

    def warn(self, event: str, trace_id: str = "", **data) -> None:
        self.log("WARN", event, trace_id, **data)

    def error(self, event: str, trace_id: str = "", **data) -> None:
        self.log("ERROR", event, trace_id, **data)

    def llm_call(self, trace_id: str, input_tokens: int,
                 output_tokens: int, latency_ms: int,
                 stop_reason: str = "") -> None:
        """记录 LLM 调用日志。"""
        self.info("llm_call", trace_id,
                  input_tokens=input_tokens,
                  output_tokens=output_tokens,
                  latency_ms=latency_ms,
                  stop_reason=stop_reason)

    def tool_call(self, trace_id: str, tool_name: str,
                  latency_ms: int) -> None:
        """记录工具调用日志。"""
        self.info("tool_call", trace_id,
                  tool=tool_name, latency_ms=latency_ms)


# ── ObservabilityManager ─────────────────────────────────────

class ObservabilityManager:
    """整合 Tracer + TokenStats + Logger 的便捷接口。"""

    def __init__(self, log_dir: str = ".logs"):
        self.tracer = Tracer()
        self.stats = TokenStats()
        self.logger = Logger(log_dir=log_dir)

    def start_turn(self) -> str:
        """开始新一轮交互，返回 trace_id。"""
        return self.tracer.new_trace()

    def record_llm_call(self, response, latency_ms: int) -> None:
        """记录 LLM 调用（从 Anthropic response 提取 token 信息）。"""
        usage = getattr(response, "usage", None)
        input_t = getattr(usage, "input_tokens", 0) if usage else 0
        output_t = getattr(usage, "output_tokens", 0) if usage else 0
        stop = getattr(response, "stop_reason", "unknown")

        self.stats.record(input_tokens=input_t, output_tokens=output_t,
                          llm_ms=latency_ms)
        self.logger.llm_call(self.tracer.trace_id, input_t, output_t,
                             latency_ms, stop)

    def record_tool_call(self, tool_name: str, latency_ms: int) -> None:
        """记录工具调用。"""
        self.stats.record_tool(tool_ms=latency_ms)
        self.logger.tool_call(self.tracer.trace_id, tool_name, latency_ms)

    def print_summary(self) -> None:
        """在终端打印统计摘要。"""
        print("\n" + "=" * 40)
        print("  📊 Session 统计")
        print("=" * 40)
        print(self.stats.summary())
        print("=" * 40)
