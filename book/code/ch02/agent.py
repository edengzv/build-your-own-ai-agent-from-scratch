"""
MiniAgent — Chapter 2: 工具调用
引入工具分发机制，Agent 现在拥有 4 个工具。

用法:
    python miniagent/agent.py "读取 README.md 的内容"
"""

import os
import sys
import subprocess
import anthropic

# --- 配置 ---
MODEL = "claude-sonnet-4-20250514"
SYSTEM = "你是一个有用的 AI 助手。你可以通过工具与计算机交互来完成任务。"

# --- 工作目录限制 ---  # NEW
WORKSPACE = os.getcwd()


def safe_path(path: str) -> str:  # NEW
    """确保路径在工作目录内，防止路径遍历攻击。"""
    resolved = os.path.realpath(os.path.join(WORKSPACE, path))
    if not resolved.startswith(os.path.realpath(WORKSPACE)):
        raise ValueError(f"路径 {path} 超出工作目录范围")
    return resolved


# --- 工具定义 ---
TOOLS = [
    {
        "name": "bash",
        "description": "在系统 shell 中执行命令。用于运行程序、管理进程、安装依赖等操作。",
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
    },
    # NEW: 文件操作工具
    {
        "name": "read_file",
        "description": "读取指定文件的完整内容。适用于查看代码、配置文件、文档等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要读取的文件路径（相对于工作目录）",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "将内容写入指定文件。如果文件不存在则创建，存在则覆盖。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要写入的文件路径（相对于工作目录）",
                },
                "content": {
                    "type": "string",
                    "description": "要写入的文件内容",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "通过查找并替换来编辑文件。old_string 必须在文件中存在且唯一。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要编辑的文件路径（相对于工作目录）",
                },
                "old_string": {
                    "type": "string",
                    "description": "要被替换的原始文本（必须在文件中唯一匹配）",
                },
                "new_string": {
                    "type": "string",
                    "description": "替换后的新文本",
                },
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
]


# --- 工具处理函数 ---
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


def handle_read_file(path: str) -> str:  # NEW
    """读取文件内容。"""
    try:
        file_path = safe_path(path)
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except ValueError as e:
        return f"[error: {e}]"
    except FileNotFoundError:
        return f"[error: 文件不存在: {path}]"
    except Exception as e:
        return f"[error: {e}]"


def handle_write_file(path: str, content: str) -> str:  # NEW
    """写入文件内容。"""
    try:
        file_path = safe_path(path)
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"已写入 {path} ({len(content)} 字符)"
    except ValueError as e:
        return f"[error: {e}]"
    except Exception as e:
        return f"[error: {e}]"


def handle_edit_file(path: str, old_string: str, new_string: str) -> str:  # NEW
    """通过查找替换编辑文件。"""
    try:
        file_path = safe_path(path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        count = content.count(old_string)
        if count == 0:
            return "[error: 未找到要替换的文本]"
        if count > 1:
            return f"[error: 找到 {count} 处匹配，需要唯一匹配]"

        new_content = content.replace(old_string, new_string, 1)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"已编辑 {path}"
    except ValueError as e:
        return f"[error: {e}]"
    except FileNotFoundError:
        return f"[error: 文件不存在: {path}]"
    except Exception as e:
        return f"[error: {e}]"


# NEW: 工具分发映射
TOOL_HANDLERS = {
    "bash": handle_bash,
    "read_file": handle_read_file,
    "write_file": handle_write_file,
    "edit_file": handle_edit_file,
}


# --- Agent 核心循环 ---
def agent_loop(messages: list) -> None:
    """Agent 的核心：一个 while 循环。"""
    client = anthropic.Anthropic()

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nAgent: {block.text}")
            return

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                handler = TOOL_HANDLERS.get(block.name)  # CHANGED: 使用分发映射
                if handler is None:
                    output = f"[error: 未知工具 {block.name}]"
                else:
                    print(f"  [Tool: {block.name}] {_summarize_input(block)}")
                    output = handler(**block.input)
                    print(f"  {output[:200]}{'...' if len(output) > 200 else ''}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })

        messages.append({"role": "user", "content": tool_results})


def _summarize_input(block) -> str:  # NEW
    """简洁地显示工具调用参数。"""
    inp = block.input
    if block.name == "bash":
        return inp.get("command", "")
    elif block.name in ("read_file", "write_file", "edit_file"):
        return inp.get("path", "")
    return str(inp)[:80]


# --- 入口 ---
def main():
    if len(sys.argv) < 2:
        print("用法: python miniagent/agent.py <你的指令>")
        print('示例: python miniagent/agent.py "读取 README.md 的内容"')
        sys.exit(1)

    user_input = " ".join(sys.argv[1:])
    messages = [{"role": "user", "content": user_input}]

    print(f"You: {user_input}")
    agent_loop(messages)


if __name__ == "__main__":
    main()
