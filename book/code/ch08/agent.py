"""
MiniAgent — Chapter 8: 后台任务
Agent 现在能让慢操作在后台执行，自己继续思考。

用法 (交互模式):
    python miniagent/agent.py

用法 (单次执行):
    python miniagent/agent.py "在后台运行测试，同时继续写代码"
"""

import os
import sys
import subprocess
import anthropic

from todo import TodoManager, TODO_TOOL, make_todo_handler
from skill_loader import (
    scan_skills,
    build_skill_summary,
    LOAD_SKILL_TOOL,
    make_load_skill_handler,
)
from context import ContextManager, COMPACT_TOOL
from subagent import run_subagent, TASK_TOOL
from background import (  # NEW
    BackgroundManager,
    BG_RUN_TOOL,
    BG_CHECK_TOOL,
    make_bg_handlers,
)

# --- 配置 ---
MODEL = "claude-sonnet-4-20250514"

# NEW: Skill 系统初始化
_skills = scan_skills()
_skill_summary = build_skill_summary(_skills)

SYSTEM_TEMPLATE = """你是 MiniAgent，一个通用 AI 助手。你可以通过工具与计算机交互来完成任务。

你的能力：
- 执行 bash 命令
- 读取、写入、编辑文件
- 管理任务列表（规划和追踪进度）
- 按需加载领域知识技能
- 管理上下文窗口，防止溢出
- 将子任务委托给子智能体执行
- 在后台执行耗时操作

规则：
- 收到复杂任务时，先用 todo 工具拆解为步骤，再逐步执行
- 每完成一个步骤，用 todo 工具更新状态
- 同一时间只处理一个任务（标记为 in_progress）
- 可以独立完成的子任务，用 task 工具委托给子智能体
- 耗时操作（测试、构建、安装等），用 bg_run 放到后台执行
- 优先使用专用文件工具，而非 bash 命令操作文件
- 需要领域知识时，用 load_skill 加载对应技能
- 当对话变长、响应变慢时，用 compact 工具压缩上下文
- 如果任务不需要工具，直接用文本回答
- 对不确定的事情，先查看再行动
""" + _skill_summary  # CHANGED: 动态追加 skill 摘要

WORKSPACE = os.getcwd()


def safe_path(path: str) -> str:
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
    TODO_TOOL,
    LOAD_SKILL_TOOL,
    COMPACT_TOOL,
    TASK_TOOL,
    BG_RUN_TOOL,    # NEW
    BG_CHECK_TOOL,  # NEW
]

# 子 Agent 的工具集（不包含 task/bg_run/bg_check）
CHILD_TOOLS = [t for t in TOOLS if t["name"] not in ("task", "bg_run", "bg_check")]


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


def handle_read_file(path: str) -> str:
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


def handle_write_file(path: str, content: str) -> str:
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


def handle_edit_file(path: str, old_string: str, new_string: str) -> str:
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


def _summarize_input(block) -> str:
    """简洁地显示工具调用参数。"""
    inp = block.input
    if block.name == "bash":
        return inp.get("command", "")
    elif block.name in ("read_file", "write_file", "edit_file"):
        return inp.get("path", "")
    elif block.name == "todo":
        action = inp.get("action", "")
        content = inp.get("content", "")
        return f"{action} {content}".strip()
    elif block.name == "load_skill":
        return inp.get("name", "")
    elif block.name == "compact":
        return "(压缩上下文)"
    elif block.name == "task":
        return inp.get("description", "")
    elif block.name == "bg_run":  # NEW
        return inp.get("command", "")[:60]
    elif block.name == "bg_check":  # NEW
        return inp.get("task_id", "(all)")
    return str(inp)[:80]


# --- Agent 核心循环 ---
def agent_loop(
    messages: list,
    todo_manager: TodoManager | None = None,
    context_manager: ContextManager | None = None,
    bg_manager: BackgroundManager | None = None,  # NEW
) -> None:
    """Agent 的核心：一个 while 循环。"""
    client = anthropic.Anthropic()

    # 构建工具处理映射
    handlers = {
        "bash": handle_bash,
        "read_file": handle_read_file,
        "write_file": handle_write_file,
        "edit_file": handle_edit_file,
        "load_skill": make_load_skill_handler(_skills),
    }
    if todo_manager is not None:
        handlers["todo"] = make_todo_handler(todo_manager)
    if context_manager is not None:
        handlers["compact"] = lambda: context_manager.handle_compact(messages, client)
    if bg_manager is not None:  # NEW
        handlers.update(make_bg_handlers(bg_manager))

    # 子 Agent 的 handler 集合
    child_handlers = {
        "bash": handle_bash,
        "read_file": handle_read_file,
        "write_file": handle_write_file,
        "edit_file": handle_edit_file,
        "load_skill": make_load_skill_handler(_skills),
    }

    def handle_task(description: str, prompt: str) -> str:
        return run_subagent(
            description=description,
            prompt=prompt,
            tools=CHILD_TOOLS,
            tool_handlers=child_handlers,
            system=SYSTEM_TEMPLATE,
        )

    handlers["task"] = handle_task

    while True:
        # 检查是否需要注入提醒
        if todo_manager is not None:
            reminder = todo_manager.tick()
            if reminder:
                messages.append({"role": "user", "content": reminder})

        # NEW: 注入后台任务完成通知
        if bg_manager is not None:
            notifications = bg_manager.drain()
            for note in notifications:
                print(f"  [Background] 任务完成通知")
                messages.append({"role": "user", "content": note})

        # 上下文压缩
        if context_manager is not None:
            context_manager.on_loop_start(messages, client)

        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_TEMPLATE,
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
                handler = handlers.get(block.name)
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


# --- 交互式 REPL ---
def repl():
    """交互式对话循环。"""
    messages = []
    todo_manager = TodoManager()
    context_manager = ContextManager()
    bg_manager = BackgroundManager()  # NEW
    print("MiniAgent REPL (输入 'exit' 退出, 'clear' 清空对话)")
    print(f"工作目录: {WORKSPACE}")
    tool_names = [t["name"] for t in TOOLS]
    print(f"工具: {', '.join(tool_names)}")
    if _skills:
        print(f"技能: {', '.join(s['name'] for s in _skills)}")
    else:
        print("技能: (未找到 skills/ 目录)")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("Bye!")
            break
        if user_input.lower() == "clear":
            messages.clear()
            todo_manager.__init__()
            context_manager.__init__()
            bg_manager.__init__()  # NEW
            print("[对话、任务和上下文已清空]")
            continue

        messages.append({"role": "user", "content": user_input})
        agent_loop(messages, todo_manager, context_manager, bg_manager)  # CHANGED


# --- 入口 ---
def main():
    if len(sys.argv) >= 2:
        user_input = " ".join(sys.argv[1:])
        messages = [{"role": "user", "content": user_input}]
        todo_manager = TodoManager()
        context_manager = ContextManager()
        bg_manager = BackgroundManager()  # NEW
        print(f"You: {user_input}")
        agent_loop(messages, todo_manager, context_manager, bg_manager)  # CHANGED
    else:
        repl()


if __name__ == "__main__":
    main()
