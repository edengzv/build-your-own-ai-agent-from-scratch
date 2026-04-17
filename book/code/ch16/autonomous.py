"""
MiniAgent — Autonomous Teammate
让队友从被动接受任务变为主动扫描任务板、认领工作。
"""

import os
import time
import json

TASKS_DIR = os.path.join(os.getcwd(), ".tasks")


def scan_claimable_tasks(role: str = "") -> list[dict]:
    """扫描 .tasks/ 目录中未认领的 pending 任务。"""
    if not os.path.exists(TASKS_DIR):
        return []
    claimable = []
    for fname in sorted(os.listdir(TASKS_DIR)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(TASKS_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                task = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if task.get("status") == "pending" and not task.get("owner"):
            claimable.append(task)
    return claimable


def claim_task(task_id: str, owner: str) -> bool:
    """原子性地认领任务。"""
    path = os.path.join(TASKS_DIR, f"{task_id}.json")
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            task = json.load(f)
        if task.get("status") != "pending" or task.get("owner"):
            return False
        task["owner"] = owner
        task["status"] = "in_progress"
        task["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        return True
    except (json.JSONDecodeError, OSError):
        return False


def complete_task(task_id: str, owner: str, result: str = "") -> bool:
    """将任务标记为完成。只有 owner 能完成。"""
    path = os.path.join(TASKS_DIR, f"{task_id}.json")
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            task = json.load(f)
        if task.get("owner") != owner:
            return False
        task["status"] = "completed"
        task["result"] = result
        task["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        _unblock_downstream(task_id)
        return True
    except (json.JSONDecodeError, OSError):
        return False


def _unblock_downstream(completed_id: str):
    """完成任务后，自动解除下游任务的阻塞。"""
    if not os.path.exists(TASKS_DIR):
        return
    for fname in os.listdir(TASKS_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(TASKS_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                task = json.load(f)
            blocked_by = task.get("blocked_by", [])
            if completed_id in blocked_by:
                blocked_by.remove(completed_id)
                task["blocked_by"] = blocked_by
                if not blocked_by and task["status"] == "blocked":
                    task["status"] = "pending"
                    task["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(task, f, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, OSError):
            continue


class AutonomousLoop:
    """队友的自主循环封装。"""

    def __init__(self, name: str, role: str, idle_timeout: float = 60.0, poll_interval: float = 5.0):
        self.name = name
        self.role = role
        self.idle_timeout = idle_timeout
        self.poll_interval = poll_interval
        self._last_activity = time.time()

    def check_and_claim(self) -> dict | None:
        tasks = scan_claimable_tasks(self.role)
        for task in tasks:
            if claim_task(task["id"], self.name):
                self._last_activity = time.time()
                return task
        return None

    def mark_complete(self, task_id: str, result: str = "") -> bool:
        success = complete_task(task_id, self.name, result)
        if success:
            self._last_activity = time.time()
        return success

    def should_shutdown(self) -> bool:
        return (time.time() - self._last_activity) > self.idle_timeout

    def reset_timer(self):
        self._last_activity = time.time()


# --- 工具 Schema ---

CLAIM_TASK_TOOL = {
    "name": "claim_task",
    "description": "认领一个 pending 状态的任务，将其标记为由我执行。",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "要认领的任务 ID"},
        },
        "required": ["task_id"],
    },
}

COMPLETE_TASK_TOOL = {
    "name": "complete_my_task",
    "description": "将我认领的任务标记为完成，附上执行结果。",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "要完成的任务 ID"},
            "result": {"type": "string", "description": "任务执行结果摘要"},
        },
        "required": ["task_id"],
    },
}

SCAN_TASKS_TOOL = {
    "name": "scan_tasks",
    "description": "扫描任务板，查看可以认领的任务。",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

AUTONOMOUS_TOOLS = [CLAIM_TASK_TOOL, COMPLETE_TASK_TOOL, SCAN_TASKS_TOOL]


def make_autonomous_handlers(auto_loop: AutonomousLoop):
    """创建自主循环的工具处理函数。"""
    def handle_claim(task_id: str) -> str:
        if claim_task(task_id, auto_loop.name):
            auto_loop.reset_timer()
            return f"已认领任务 {task_id}"
        return f"[error: 无法认领任务 {task_id}（可能已被认领）]"

    def handle_complete(task_id: str, result: str = "") -> str:
        if auto_loop.mark_complete(task_id, result):
            return f"任务 {task_id} 已完成"
        return f"[error: 无法完成任务 {task_id}（你不是 owner？）]"

    def handle_scan() -> str:
        tasks = scan_claimable_tasks()
        if not tasks:
            return "没有可认领的任务"
        lines = []
        for t in tasks:
            lines.append(f"  {t['id']}: {t.get('description', '(无描述)')}")
        sep = chr(10)
        return f"可认领的任务 ({len(tasks)} 个):{sep}" + sep.join(lines)

    return {
        "claim_task": handle_claim,
        "complete_my_task": handle_complete,
        "scan_tasks": handle_scan,
    }
