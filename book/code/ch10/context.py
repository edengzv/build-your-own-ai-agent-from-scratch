"""
MiniAgent — Context Manager
三层上下文压缩策略，让 Agent 能处理任意长度的任务。

Layer 1 (micro_compact): 每轮自动替换旧 tool_result 为摘要占位符
Layer 2 (auto_compact):  当 token 估算超过阈值时，LLM 自动生成摘要
Layer 3 (manual compact): Agent 主动调用 compact 工具
"""

import os
import json
import time

# 简单的 token 估算：1 token ≈ 4 个字符（英文），中文约 1.5 字符/token
# 这是粗略估算，足够用于触发压缩
TOKEN_CHAR_RATIO = 3  # 取中间值
AUTO_COMPACT_THRESHOLD = 50000  # tokens
MICRO_COMPACT_AGE = 3  # 超过 N 轮的 tool_result 会被压缩
TRANSCRIPTS_DIR = os.path.join(os.getcwd(), ".transcripts")


def estimate_tokens(messages: list) -> int:
    """粗略估算消息列表的 token 数。"""
    total_chars = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total_chars += len(str(block))
                else:
                    total_chars += len(str(block))
    return total_chars // TOKEN_CHAR_RATIO


def micro_compact(messages: list, current_round: int) -> int:
    """
    Layer 1: 将旧的 tool_result 替换为摘要占位符。
    返回压缩的 tool_result 数量。
    """
    compacted = 0
    round_counter = 0

    for i, msg in enumerate(messages):
        if msg["role"] == "user" and isinstance(msg.get("content"), list):
            # 这是一个 tool_result 消息
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


def auto_compact(messages: list, client) -> list:
    """
    Layer 2: 当 token 数超过阈值时，让 LLM 生成摘要并替换所有消息。
    返回压缩后的新消息列表。
    """
    # 保存完整记录到 .transcripts/
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    transcript_file = os.path.join(
        TRANSCRIPTS_DIR, f"transcript_{int(time.time())}.json"
    )

    # 序列化消息（处理不可 JSON 序列化的对象）
    serializable = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            serializable.append(msg)
        else:
            serializable.append({
                "role": msg["role"],
                "content": str(content),
            })

    with open(transcript_file, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

    # 让 LLM 总结当前对话
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

    summary_text = ""
    for block in summary_response.content:
        if hasattr(block, "text"):
            summary_text += block.text

    # 用摘要替换所有消息
    new_messages = [
        {
            "role": "user",
            "content": (
                f"[上下文压缩] 以下是之前对话的摘要:\n\n{summary_text}\n\n"
                f"完整记录已保存到: {transcript_file}\n"
                "请基于这个摘要继续工作。"
            ),
        },
        {
            "role": "assistant",
            "content": "好的，我已了解之前的对话内容。请继续。",
        },
    ]

    return new_messages


def manual_compact(messages: list, client) -> str:
    """
    Layer 3: Agent 主动触发的压缩。
    """
    token_before = estimate_tokens(messages)
    new_messages = auto_compact(messages, client)
    token_after = estimate_tokens(new_messages)

    # 就地替换 messages 内容
    messages.clear()
    messages.extend(new_messages)

    return (
        f"上下文已压缩: {token_before} → {token_after} tokens "
        f"(节省 {token_before - token_after} tokens)"
    )


# --- 工具 Schema ---
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
