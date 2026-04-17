"""
MiniAgent — Chapter 1: 你好，Agent
一个不到 30 行核心代码的 AI Agent。

用法:
    python miniagent/agent.py "列出当前目录的文件"
"""

import os
import sys
import subprocess
import anthropic

# --- 配置 ---
MODEL = "claude-sonnet-4-20250514"
SYSTEM = "你是一个有用的 AI 助手。你可以通过工具与计算机交互来完成任务。"

# --- 工具定义 ---
TOOLS = [
    {
        "name": "bash",
        "description": "在系统 shell 中执行命令。用于运行程序、查看文件列表、安装依赖等操作。",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的 bash 命令",
                }
            },
            "required": ["command"],
        },
    }
]


# --- 工具处理 ---
def handle_bash(command: str) -> str:
    """执行 bash 命令并返回输出。"""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout
        if result.returncode != 0:
            output += f"\n[stderr]\n{result.stderr}" if result.stderr else ""
            output += f"\n[exit code: {result.returncode}]"
        return output if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return "[error: command timed out after 30s]"


# --- Agent 核心循环 ---
def agent_loop(messages: list) -> None:
    """Agent 的核心：一个 while 循环。"""
    client = anthropic.Anthropic()

    while True:
        # 1. 发送消息给 LLM
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
        )

        # 2. 把 LLM 的回复追加到消息列表
        messages.append({"role": "assistant", "content": response.content})

        # 3. 如果 LLM 没有请求工具调用，结束循环
        if response.stop_reason != "tool_use":
            # 输出 LLM 的文本回复
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nAgent: {block.text}")
            return

        # 4. 执行 LLM 请求的工具
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [Tool: {block.name}] {block.input.get('command', '')}")
                output = handle_bash(**block.input)
                print(f"  {output[:200]}{'...' if len(output) > 200 else ''}")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                    }
                )

        # 5. 把工具结果送回 LLM，继续循环
        messages.append({"role": "user", "content": tool_results})


# --- 入口 ---
def main():
    if len(sys.argv) < 2:
        print("用法: python miniagent/agent.py <你的指令>")
        print('示例: python miniagent/agent.py "列出当前目录的文件"')
        sys.exit(1)

    user_input = " ".join(sys.argv[1:])
    messages = [{"role": "user", "content": user_input}]

    print(f"You: {user_input}")
    agent_loop(messages)


if __name__ == "__main__":
    main()
