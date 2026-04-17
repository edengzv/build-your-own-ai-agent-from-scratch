"""
MiniAgent — TodoManager
任务规划与进度追踪。

Agent 通过 todo 工具管理任务列表：
- 添加任务
- 更新任务状态 (pending → in_progress → completed)
- 列出所有任务

约束：同一时间只能有一个 in_progress 的任务。
"""

import json

VALID_STATUSES = ("pending", "in_progress", "completed")


class TodoManager:
    """内存中的任务列表管理器。"""

    def __init__(self):
        self.todos: list[dict] = []
        self._rounds_since_update = 0  # 用于提醒机制

    def add(self, content: str) -> str:
        """添加一个新的待办事项。"""
        todo = {
            "id": len(self.todos) + 1,
            "content": content,
            "status": "pending",
        }
        self.todos.append(todo)
        self._rounds_since_update = 0
        return f"已添加任务 #{todo['id']}: {content}"

    def update_status(self, todo_id: int, status: str) -> str:
        """更新任务状态。"""
        if status not in VALID_STATUSES:
            return f"[error: 无效状态 '{status}'，有效值: {', '.join(VALID_STATUSES)}]"

        todo = self._find(todo_id)
        if todo is None:
            return f"[error: 任务 #{todo_id} 不存在]"

        # 约束：同一时间只能有一个 in_progress
        if status == "in_progress":
            current_wip = [t for t in self.todos if t["status"] == "in_progress"]
            if current_wip and current_wip[0]["id"] != todo_id:
                return (
                    f"[error: 任务 #{current_wip[0]['id']} 正在进行中。"
                    f"请先完成它，再开始新任务]"
                )

        old_status = todo["status"]
        todo["status"] = status
        self._rounds_since_update = 0
        return f"任务 #{todo_id}: {old_status} → {status}"

    def list_todos(self) -> str:
        """列出所有任务及其状态。"""
        if not self.todos:
            return "任务列表为空。"

        lines = ["任务列表:"]
        status_icons = {"pending": "○", "in_progress": "◉", "completed": "✓"}
        for t in self.todos:
            icon = status_icons.get(t["status"], "?")
            lines.append(f"  {icon} #{t['id']} [{t['status']}] {t['content']}")

        # 统计
        total = len(self.todos)
        done = sum(1 for t in self.todos if t["status"] == "completed")
        lines.append(f"\n进度: {done}/{total} 已完成")
        return "\n".join(lines)

    def tick(self) -> str | None:
        """每轮调用一次。如果 Agent 连续多轮未更新 todo，返回提醒消息。"""
        self._rounds_since_update += 1
        if self._rounds_since_update >= 3 and self.todos:
            pending = [t for t in self.todos if t["status"] != "completed"]
            if pending:
                return (
                    "<reminder>你有未完成的任务。请用 todo 工具更新进度，"
                    "或标记当前任务为 completed。</reminder>"
                )
        return None

    def _find(self, todo_id: int) -> dict | None:
        for t in self.todos:
            if t["id"] == todo_id:
                return t
        return None


# --- 工具 Schema ---
TODO_TOOL = {
    "name": "todo",
    "description": (
        "管理任务列表。用于规划多步骤任务、追踪进度。"
        "在开始复杂任务前，先用 add 拆解步骤；执行时用 update_status 更新状态。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "update_status", "list"],
                "description": "操作类型: add(添加任务), update_status(更新状态), list(列出所有)",
            },
            "content": {
                "type": "string",
                "description": "任务内容 (action=add 时必填)",
            },
            "todo_id": {
                "type": "integer",
                "description": "任务 ID (action=update_status 时必填)",
            },
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed"],
                "description": "目标状态 (action=update_status 时必填)",
            },
        },
        "required": ["action"],
    },
}


def make_todo_handler(manager: TodoManager):
    """创建绑定到特定 TodoManager 实例的 handler 函数。"""

    def handle_todo(action: str, **kwargs) -> str:
        if action == "add":
            content = kwargs.get("content", "")
            if not content:
                return "[error: 缺少 content 参数]"
            return manager.add(content)
        elif action == "update_status":
            todo_id = kwargs.get("todo_id")
            status = kwargs.get("status", "")
            if todo_id is None:
                return "[error: 缺少 todo_id 参数]"
            return manager.update_status(int(todo_id), status)
        elif action == "list":
            return manager.list_todos()
        else:
            return f"[error: 未知操作 '{action}'，有效值: add, update_status, list]"

    return handle_todo
