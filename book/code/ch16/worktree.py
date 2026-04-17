"""
MiniAgent — Worktree Manager
Git Worktree 绑定任务，为每个队友提供隔离的工作目录。
"""

import os
import json
import time
import subprocess

WORKTREES_DIR = os.path.join(os.getcwd(), ".worktrees")
EVENTS_FILE = os.path.join(WORKTREES_DIR, "events.jsonl")


class WorktreeManager:
    """管理 Git Worktree 的生命周期。"""

    def __init__(self, base_dir: str = ""):
        self._base_dir = base_dir or os.getcwd()
        os.makedirs(WORKTREES_DIR, exist_ok=True)

    def _log_event(self, event_type: str, task_id: str, **extra):
        event = {
            "type": event_type,
            "task_id": task_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            **extra,
        }
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def create(self, task_id: str, branch: str = "") -> str:
        """为任务创建一个隔离的 worktree。"""
        if not branch:
            branch = f"task-{task_id}"
        wt_path = os.path.join(WORKTREES_DIR, task_id)
        if os.path.exists(wt_path):
            return f"[error: worktree '{task_id}' 已存在于 {wt_path}]"
        try:
            subprocess.run(
                ["git", "branch", branch],
                cwd=self._base_dir, capture_output=True, text=True,
            )
            result = subprocess.run(
                ["git", "worktree", "add", wt_path, branch],
                cwd=self._base_dir, capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return f"[error: git worktree add 失败: {result.stderr.strip()}]"
            self._log_event("created", task_id, path=wt_path, branch=branch)
            return wt_path
        except subprocess.TimeoutExpired:
            return "[error: git worktree 操作超时]"
        except Exception as e:
            return f"[error: {e}]"

    def remove(self, task_id: str, keep: bool = False) -> str:
        """移除 worktree。"""
        wt_path = os.path.join(WORKTREES_DIR, task_id)
        if not os.path.exists(wt_path):
            return f"[error: worktree '{task_id}' 不存在]"
        try:
            result = subprocess.run(
                ["git", "worktree", "remove", wt_path, "--force"],
                cwd=self._base_dir, capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return f"[error: git worktree remove 失败: {result.stderr.strip()}]"
            event_type = "kept" if keep else "removed"
            self._log_event(event_type, task_id, path=wt_path)
            return f"worktree '{task_id}' 已移除"
        except Exception as e:
            return f"[error: {e}]"

    def get_path(self, task_id: str) -> str | None:
        wt_path = os.path.join(WORKTREES_DIR, task_id)
        if os.path.exists(wt_path):
            return wt_path
        return None

    def list_worktrees(self) -> str:
        """列出所有活跃的 worktree。"""
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self._base_dir, capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return f"[error: {result.stderr.strip()}]"
            lines = []
            current_path = ""
            current_branch = ""
            for line in result.stdout.strip().split("\n"):
                if line.startswith("worktree "):
                    current_path = line.split(" ", 1)[1]
                elif line.startswith("branch "):
                    current_branch = line.split(" ", 1)[1].replace("refs/heads/", "")
                elif line == "":
                    if WORKTREES_DIR in current_path:
                        task_id = os.path.basename(current_path)
                        lines.append(f"  {task_id}: [{current_branch}] {current_path}")
                    current_path = ""
                    current_branch = ""
            if current_path and WORKTREES_DIR in current_path:
                task_id = os.path.basename(current_path)
                lines.append(f"  {task_id}: [{current_branch}] {current_path}")
            if not lines:
                return "没有活跃的 worktree"
            return "\n".join(lines)
        except Exception as e:
            return f"[error: {e}]"

    def get_events(self, task_id: str = "") -> str:
        if not os.path.exists(EVENTS_FILE):
            return "没有事件记录"
        events = []
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    if task_id and event.get("task_id") != task_id:
                        continue
                    events.append(event)
                except json.JSONDecodeError:
                    continue
        if not events:
            return "没有事件记录"
        lines = []
        for e in events:
            lines.append(f"  [{e['timestamp']}] {e['type']}: {e['task_id']}")
        return "\n".join(lines)


# --- 工具 Schema ---

CREATE_WT_TOOL = {
    "name": "worktree_create",
    "description": "为任务创建隔离的 Git Worktree 工作目录。",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "要绑定的任务 ID"},
            "branch": {"type": "string", "description": "分支名称"},
        },
        "required": ["task_id"],
    },
}

REMOVE_WT_TOOL = {
    "name": "worktree_remove",
    "description": "移除任务的 worktree。",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "要移除的 worktree 的任务 ID"},
            "keep": {"type": "boolean", "description": "是否保留分支"},
        },
        "required": ["task_id"],
    },
}

LIST_WT_TOOL = {
    "name": "worktree_list",
    "description": "列出所有活跃的 worktree。",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

WORKTREE_TOOLS = [CREATE_WT_TOOL, REMOVE_WT_TOOL, LIST_WT_TOOL]


def make_worktree_handlers(wt_manager: WorktreeManager):
    """创建 worktree 工具处理函数。"""
    return {
        "worktree_create": lambda task_id, branch="": wt_manager.create(task_id, branch),
        "worktree_remove": lambda task_id, keep=False: wt_manager.remove(task_id, keep),
        "worktree_list": lambda: wt_manager.list_worktrees(),
    }
