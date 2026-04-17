"""
MiniAgent — Task Graph (持久化任务图)
文件级任务 DAG：支持依赖关系、持久化、跨会话保持。

每个任务存为 .tasks/{id}.json，包含：
    id, description, status, blocked_by, owner, created_at, updated_at

用法：
    tg = TaskGraph()
    tg.create("实现登录功能", blocked_by=["task_1"])
    tg.update_status("task_2", "in_progress")
    tg.list_tasks()
"""

import os
import json
import time

TASKS_DIR = os.path.join(os.getcwd(), ".tasks")


class TaskGraph:
    """文件级任务 DAG。每个任务一个 JSON 文件。"""

    def __init__(self, tasks_dir: str = TASKS_DIR):
        self._tasks_dir = tasks_dir
        os.makedirs(self._tasks_dir, exist_ok=True)
        self._counter = self._find_max_id()

    def _find_max_id(self) -> int:
        """找到当前最大的任务 ID 编号。"""
        max_id = 0
        if os.path.isdir(self._tasks_dir):
            for fname in os.listdir(self._tasks_dir):
                if fname.startswith("task_") and fname.endswith(".json"):
                    try:
                        num = int(fname[5:-5])
                        max_id = max(max_id, num)
                    except ValueError:
                        continue
        return max_id

    def _task_path(self, task_id: str) -> str:
        return os.path.join(self._tasks_dir, f"{task_id}.json")

    def _load(self, task_id: str) -> dict | None:
        path = self._task_path(task_id)
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, task: dict) -> None:
        task["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        path = self._task_path(task["id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(task, f, ensure_ascii=False, indent=2)

    def create(
        self,
        description: str,
        blocked_by: list[str] | None = None,
        owner: str = "",
    ) -> str:
        """创建新任务，返回 task_id。"""
        self._counter += 1
        task_id = f"task_{self._counter}"

        # 验证 blocked_by 中的任务存在
        if blocked_by:
            for dep_id in blocked_by:
                if self._load(dep_id) is None:
                    return f"[error: 依赖任务 {dep_id} 不存在]"

        task = {
            "id": task_id,
            "description": description,
            "status": "blocked" if blocked_by else "pending",
            "blocked_by": blocked_by or [],
            "owner": owner,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._save(task)
        return task_id

    def update_status(self, task_id: str, status: str) -> str:
        """更新任务状态。完成任务时自动解除下游阻塞。"""
        valid_statuses = ("pending", "in_progress", "completed", "blocked", "failed")
        if status not in valid_statuses:
            return f"[error: 无效状态 '{status}'。有效: {', '.join(valid_statuses)}]"

        task = self._load(task_id)
        if task is None:
            return f"[error: 任务 {task_id} 不存在]"

        if task["status"] == "blocked" and status == "in_progress":
            # 检查是否还有未完成的依赖
            for dep_id in task["blocked_by"]:
                dep = self._load(dep_id)
                if dep and dep["status"] != "completed":
                    return f"[error: 任务 {task_id} 被 {dep_id} 阻塞，无法开始]"

        old_status = task["status"]
        task["status"] = status
        self._save(task)

        # 完成时自动解除下游阻塞
        unblocked = []
        if status == "completed":
            unblocked = self._unblock_downstream(task_id)

        result = f"任务 {task_id}: {old_status} → {status}"
        if unblocked:
            result += f"\n自动解除阻塞: {', '.join(unblocked)}"
        return result

    def _unblock_downstream(self, completed_id: str) -> list[str]:
        """当一个任务完成时，检查并解除下游阻塞。"""
        unblocked = []
        for fname in os.listdir(self._tasks_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._tasks_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                task = json.load(f)

            if task["status"] != "blocked":
                continue
            if completed_id not in task.get("blocked_by", []):
                continue

            # 检查是否所有依赖都已完成
            all_done = True
            for dep_id in task["blocked_by"]:
                dep = self._load(dep_id)
                if dep and dep["status"] != "completed":
                    all_done = False
                    break

            if all_done:
                task["status"] = "pending"
                self._save(task)
                unblocked.append(task["id"])

        return unblocked

    def get(self, task_id: str) -> str:
        """获取任务详情。"""
        task = self._load(task_id)
        if task is None:
            return f"[error: 任务 {task_id} 不存在]"
        return json.dumps(task, ensure_ascii=False, indent=2)

    def list_tasks(self, status_filter: str = "") -> str:
        """列出所有任务（可按状态过滤）。"""
        tasks = []
        if not os.path.isdir(self._tasks_dir):
            return "没有任务"
        for fname in sorted(os.listdir(self._tasks_dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._tasks_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                task = json.load(f)
            if status_filter and task["status"] != status_filter:
                continue
            tasks.append(task)

        if not tasks:
            return f"没有{'状态为 ' + status_filter + ' 的' if status_filter else ''}任务"

        lines = []
        for t in tasks:
            deps = f" (blocked by: {', '.join(t['blocked_by'])})" if t["blocked_by"] else ""
            owner = f" @{t['owner']}" if t["owner"] else ""
            lines.append(f"  {t['id']}: [{t['status']}] {t['description']}{deps}{owner}")
        return "\n".join(lines)


# --- 工具 Schema ---
TASK_CREATE_TOOL = {
    "name": "task_create",
    "description": "创建一个新任务。可指定依赖关系（blocked_by）和负责人（owner）。",
    "input_schema": {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "任务描述",
            },
            "blocked_by": {
                "type": "array",
                "items": {"type": "string"},
                "description": "阻塞此任务的前置任务 ID 列表（如 ['task_1', 'task_2']）",
            },
            "owner": {
                "type": "string",
                "description": "任务负责人（可选）",
            },
        },
        "required": ["description"],
    },
}

TASK_UPDATE_TOOL = {
    "name": "task_update",
    "description": "更新任务状态。完成任务时会自动解除下游的阻塞。",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "任务 ID（如 task_1）",
            },
            "status": {
                "type": "string",
                "description": "新状态: pending, in_progress, completed, failed",
            },
        },
        "required": ["task_id", "status"],
    },
}

TASK_LIST_TOOL = {
    "name": "task_list",
    "description": "列出所有任务。可按状态过滤。",
    "input_schema": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "过滤状态（可选）: pending, in_progress, completed, blocked, failed",
            },
        },
        "required": [],
    },
}

TASK_GET_TOOL = {
    "name": "task_get",
    "description": "获取指定任务的完整详情。",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "任务 ID",
            },
        },
        "required": ["task_id"],
    },
}

TASK_GRAPH_TOOLS = [TASK_CREATE_TOOL, TASK_UPDATE_TOOL, TASK_LIST_TOOL, TASK_GET_TOOL]


def make_task_graph_handlers(tg: "TaskGraph") -> dict:
    """创建绑定到 TaskGraph 实例的 handler 字典。"""

    def handle_task_create(description: str, blocked_by: list = None, owner: str = "") -> str:
        task_id = tg.create(description, blocked_by=blocked_by, owner=owner)
        if task_id.startswith("[error"):
            return task_id
        task = tg.get(task_id)
        return f"已创建任务 {task_id}\n{task}"

    def handle_task_update(task_id: str, status: str) -> str:
        return tg.update_status(task_id, status)

    def handle_task_list(status: str = "") -> str:
        return tg.list_tasks(status_filter=status)

    def handle_task_get(task_id: str) -> str:
        return tg.get(task_id)

    return {
        "task_create": handle_task_create,
        "task_update": handle_task_update,
        "task_list": handle_task_list,
        "task_get": handle_task_get,
    }
