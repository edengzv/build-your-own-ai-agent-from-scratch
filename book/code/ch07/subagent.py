"""
MiniAgent — Subagent
独立的子智能体：拥有干净的上下文，完成后只返回精炼结果。

用法：
    result = run_subagent(
        description="分析 auth.py 的安全性",
        prompt="读取 auth.py 并找出所有安全隐患",
        tools=CHILD_TOOLS,
        system=SYSTEM_TEMPLATE,
    )
"""

import anthropic

# 子 Agent 默认使用与父 Agent 相同的模型
MODEL = "claude-sonnet-4-20250514"


def run_subagent(
    description: str,
    prompt: str,
    tools: list,
    tool_handlers: dict,
    system: str,
    model: str = MODEL,
    max_turns: int = 20,
) -> str:
    """
    启动一个独立的子 Agent，在干净的上下文中执行任务。

    Args:
        description: 任务简述（用于日志显示）
        prompt: 交给子 Agent 的完整提示
        tools: 子 Agent 可用的工具列表（不应包含 task 工具）
        tool_handlers: 工具名 → handler 函数的映射
        system: 系统提示
        model: 使用的模型
        max_turns: 最大循环轮数（防止无限循环）

    Returns:
        子 Agent 的最终文本回复
    """
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": prompt}]

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

        # 子 Agent 完成——提取文本回复
        if response.stop_reason != "tool_use":
            result_parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    result_parts.append(block.text)
            result = "\n".join(result_parts) if result_parts else "(子 Agent 无文本输出)"
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
                    print(f"    [Sub-Tool: {block.name}] {_sub_summarize(block)}")
                    output = handler(**block.input)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })

        messages.append({"role": "user", "content": tool_results})

    return f"[warning: 子 Agent 达到最大轮次 {max_turns}，强制终止]"


def _sub_summarize(block) -> str:
    """子 Agent 工具调用的简要日志。"""
    inp = block.input
    if block.name == "bash":
        return inp.get("command", "")[:60]
    elif block.name in ("read_file", "write_file", "edit_file"):
        return inp.get("path", "")
    return str(inp)[:60]


# --- 工具 Schema ---
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
                "description": "子任务的简短描述（用于日志和进度追踪）",
            },
            "prompt": {
                "type": "string",
                "description": "交给子智能体的完整任务指令",
            },
        },
        "required": ["description", "prompt"],
    },
}
