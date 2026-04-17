"""
MiniAgent — Background Manager
后台任务管理器：让慢操作异步执行，Agent 继续思考。

用法：
    mgr = BackgroundManager()
    task_id = mgr.start("pytest tests/", timeout=120)
    status = mgr.check(task_id)
    notifications = mgr.drain()  # 获取已完成的任务通知
"""

import subprocess
import threading
import time
from dataclasses import dataclass, field


@dataclass
class BgTask:
    """一个后台任务的状态。"""
    task_id: str
    command: str
    status: str = "running"  # running | completed | failed | timed_out
    output: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None


class BackgroundManager:
    """管理后台进程的执行和通知。"""

    def __init__(self):
        self._tasks: dict[str, BgTask] = {}
        self._notifications: list[str] = []
        self._lock = threading.Lock()
        self._counter = 0

    def start(self, command: str, timeout: int = 120) -> str:
        """启动后台命令，立即返回 task_id。"""
        with self._lock:
            self._counter += 1
            task_id = f"bg_{self._counter}"

        task = BgTask(task_id=task_id, command=command)
        with self._lock:
            self._tasks[task_id] = task

        # 在独立线程中执行命令
        thread = threading.Thread(
            target=self._run_command,
            args=(task, timeout),
            daemon=True,
        )
        thread.start()

        return task_id

    def _run_command(self, task: BgTask, timeout: int) -> None:
        """在后台线程中执行命令。"""
        try:
            result = subprocess.run(
                task.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = result.stdout
            if result.returncode != 0:
                output += f"\n[stderr]\n{result.stderr}" if result.stderr else ""
                output += f"\n[exit code: {result.returncode}]"
                status = "failed"
            else:
                status = "completed"

            with self._lock:
                task.status = status
                task.output = output if output.strip() else "(no output)"
                task.end_time = time.time()
                elapsed = task.end_time - task.start_time
                self._notifications.append(
                    f"<background-result task_id='{task.task_id}' "
                    f"status='{status}' elapsed='{elapsed:.1f}s'>\n"
                    f"命令: {task.command}\n"
                    f"输出:\n{task.output[:2000]}\n"
                    f"</background-result>"
                )

        except subprocess.TimeoutExpired:
            with self._lock:
                task.status = "timed_out"
                task.output = f"[error: 命令超时 ({timeout}s)]"
                task.end_time = time.time()
                self._notifications.append(
                    f"<background-result task_id='{task.task_id}' "
                    f"status='timed_out'>\n"
                    f"命令: {task.command}\n"
                    f"[超时: {timeout}s]\n"
                    f"</background-result>"
                )

    def check(self, task_id: str) -> str:
        """检查指定任务的状态。"""
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            return f"[error: 未找到任务 {task_id}]"

        elapsed = (task.end_time or time.time()) - task.start_time
        info = f"任务 {task_id}: {task.status} ({elapsed:.1f}s)\n命令: {task.command}"
        if task.status != "running":
            info += f"\n输出:\n{task.output[:2000]}"
        return info

    def drain(self) -> list[str]:
        """获取并清空所有待处理的通知。"""
        with self._lock:
            notifications = self._notifications[:]
            self._notifications.clear()
        return notifications

    def list_tasks(self) -> str:
        """列出所有后台任务。"""
        with self._lock:
            tasks = list(self._tasks.values())
        if not tasks:
            return "没有后台任务"
        lines = []
        for t in tasks:
            elapsed = (t.end_time or time.time()) - t.start_time
            lines.append(f"  {t.task_id}: [{t.status}] {t.command} ({elapsed:.1f}s)")
        return "\n".join(lines)


# --- 工具 Schema ---
BG_RUN_TOOL = {
    "name": "bg_run",
    "description": (
        "在后台启动一个命令。立即返回任务 ID，不等待完成。"
        "适用于耗时操作：测试套件、安装依赖、构建项目等。"
        "完成后结果会自动通知你。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要在后台执行的 bash 命令",
            },
            "timeout": {
                "type": "integer",
                "description": "超时时间（秒），默认 120",
            },
        },
        "required": ["command"],
    },
}

BG_CHECK_TOOL = {
    "name": "bg_check",
    "description": "检查后台任务的状态和输出。传入 task_id 检查特定任务，或不传查看所有任务。",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "要检查的任务 ID（如 bg_1）。不传则列出所有任务。",
            },
        },
        "required": [],
    },
}


def make_bg_handlers(bg_manager: "BackgroundManager") -> dict:
    """创建绑定到 BackgroundManager 实例的 handler 字典。"""

    def handle_bg_run(command: str, timeout: int = 120) -> str:
        task_id = bg_manager.start(command, timeout=timeout)
        return f"后台任务已启动: {task_id}\n命令: {command}\n完成后会自动通知你。"

    def handle_bg_check(task_id: str = "") -> str:
        if task_id:
            return bg_manager.check(task_id)
        return bg_manager.list_tasks()

    return {
        "bg_run": handle_bg_run,
        "bg_check": handle_bg_check,
    }
