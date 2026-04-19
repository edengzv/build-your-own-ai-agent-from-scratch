<!-- Translated from: ch13-work-isolation.md -->

# Chapter 13: Work Isolation

> **Motto**: "Each works in their own directory, undisturbed by the others."

> The previous chapter taught teammates to autonomously claim tasks. But a serious problem was left unaddressed — multiple teammates working in the same directory. If two teammates edit `app.py` at the same time, one's changes get overwritten by the other. This chapter introduces a mechanism that binds tasks to Git Worktrees, giving each teammate their own independent working directory.

![Conceptual: Security shield dome](images/ch13/fig-13-01-concept.png)

*Figure 13-1. Work isolation: each teammate operates in their own independent workspace.*

## The Problem

```
Lead: [Tool: spawn] reviewer (代码审查员)
      [Tool: spawn] developer (开发者)
      [Tool: send] → reviewer：审查 app.py
      [Tool: send] → developer：重构 app.py

reviewer: [Tool: read_file] app.py → 读取到版本 A
developer: [Tool: edit_file] app.py → 将版本 A 改为版本 B

reviewer: [Tool: edit_file] app.py → 将版本 A 改为版本 C
  → [error: 未找到要替换的文本]  💥
```

The reviewer read version A, but the developer has already changed the file to version B. The reviewer's edit is based on a stale version — the `old_string` no longer exists.

An even worse scenario: two teammates use `write_file` on the same file simultaneously — the one who writes last silently overwrites the first, and data is lost.

This is **multi-agent file conflict** — the exact same problem human developers face when they work directly on main without branches.

## The Solution

We introduce separation at **two levels**:

```
控制面（不变）          执行面（隔离）
.tasks/                .worktrees/
├── task_1.json        ├── task_1/     ← reviewer 的工作目录
├── task_2.json        ├── task_2/     ← developer 的工作目录
└── task_3.json        └── events.jsonl
```

- **Control plane** (`.tasks/`): Stores goals and state — what to do, who is doing it, how far along it is
- **Execution plane** (`.worktrees/`): Provides isolated work environments — one Git Worktree per task

Git Worktree is a native Git feature: it creates multiple working directories from the same repository, each with its own branch, but sharing the same `.git` history. It is far more efficient than copying the entire directory.

## 13.1 WorktreeManager

```python
class WorktreeManager:
    def __init__(self, base_dir=""):
        self._base_dir = base_dir or os.getcwd()
        os.makedirs(WORKTREES_DIR, exist_ok=True)
```

**Creating a Worktree**:

```python
def create(self, task_id, branch=""):
    if not branch:
        branch = f"task-{task_id}"

    wt_path = os.path.join(WORKTREES_DIR, task_id)

    # 创建新分支（从当前 HEAD）
    subprocess.run(["git", "branch", branch], cwd=self._base_dir, ...)
    # 创建 worktree
    subprocess.run(
        ["git", "worktree", "add", wt_path, branch],
        cwd=self._base_dir, ...
    )

    self._log_event("created", task_id, path=wt_path, branch=branch)
    return wt_path
```

Each worktree is a complete working directory — it has its own file tree, its own branch, and can commit independently. But they all share the same Git object store (`.git/`), so creation is extremely fast.

**Removing a Worktree**:

```python
def remove(self, task_id, keep=False):
    subprocess.run(
        ["git", "worktree", "remove", wt_path, "--force"],
        cwd=self._base_dir, ...
    )
```

`keep=True` preserves the branch (so it can be merged later). `keep=False` cleans up completely.

## 13.2 Event Log

Every worktree lifecycle event is recorded in `.worktrees/events.jsonl`:

```json
{"type": "created", "task_id": "task_1", "timestamp": "...", "branch": "task-task_1"}
{"type": "removed", "task_id": "task_1", "timestamp": "..."}
```

State machine: `absent -> created -> removed | kept`

This gives you an audit trail — you can review which worktrees were active at any point in time.

## 13.3 Three Tools

| Tool | Function | User |
|---|---|---|
| `worktree_create` | Creates an isolated working directory for a task | Lead |
| `worktree_remove` | Removes a worktree after the task is done | Lead |
| `worktree_list` | Lists all active worktrees | Lead |

These three tools are Lead-exclusive — teammates do not need to manage worktrees themselves. The Lead creates them when assigning tasks and cleans them up when work is done.

## 13.4 Integrating into the Agent

```python
from worktree import WorktreeManager, WORKTREE_TOOLS, make_worktree_handlers

TOOLS = [
    ...已有工具...,
    *WORKTREE_TOOLS,  # NEW
]

_PARENT_ONLY = {
    ...,
    "worktree_create", "worktree_remove", "worktree_list",  # NEW
}
```

The `agent_loop` gains a `wt_manager` parameter:

```python
def agent_loop(messages, ..., wt_manager=None):
    if wt_manager is not None:
        handlers.update(make_worktree_handlers(wt_manager))
```

## 13.5 The Workflow

Here is the complete isolation workflow:

```
1. Lead: task_create("实现 API") → task_1
2. Lead: worktree_create("task_1") → .worktrees/task_1/
3. Lead: spawn("developer") 
4. Lead: send("developer", "在 .worktrees/task_1/ 中实现 API")
5. developer: 在隔离目录中工作... commit 到 task-task_1 分支
6. developer: complete_my_task("task_1")
7. Lead: worktree_remove("task_1", keep=True)  # 保留分支用于 review
8. Lead: git merge task-task_1  # 合并回主分支
```

Each teammate works on their own branch, and when they are done, changes are merged back via Git merge. Conflicts are resolved at merge time — not by silently overwriting each other during edits.

## 13.6 Try It Out

```bash
cd miniagent
python agent.py
```

```
工具: bash, read_file, write_file, edit_file, todo, load_skill, compact, task,
      bg_run, bg_check, task_create, task_update, task_list, task_get,
      spawn, send, inbox, team_status,
      shutdown_request, plan_review, protocol_list,
      worktree_create, worktree_remove, worktree_list
```

Try creating isolated work environments:

```
You: 创建两个任务，为每个任务创建 worktree，然后列出所有 worktree
```

```
You: 查看 .worktrees/ 目录结构
```

> **Try It Yourself**: Go into the `.worktrees/task_1/` directory and run `git branch` to see the current branch. You will see it is on the `task-task_1` branch, completely isolated from the main directory.

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +15 行（worktree 导入、handler 注册）
├── todo.py
├── skill_loader.py
├── context.py
├── subagent.py
├── background.py
├── tasks.py
├── team.py
├── protocols.py
├── autonomous.py
├── worktree.py         ← NEW: 185 行（WorktreeManager、事件日志、3 个工具）
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| Metric | Chapter 12 | Chapter 13 |
|------|------------|------------|
| Tool count | 21 | **24** (+worktree_create, +worktree_remove, +worktree_list) |
| Module count | 10 | **11** (+worktree.py) |
| Capability | Autonomous claiming | **+Git Worktree isolation** |
| File safety | Possible conflicts | **Branch isolation** |

**Part IV is complete**. Your multi-agent system now has a full suite of collaboration capabilities:

- **Team** (ch10): Persistent teammates + mailbox communication
- **Protocols** (ch11): Safe shutdown + plan approval
- **Autonomy** (ch12): Task scanning + automatic claiming
- **Isolation** (ch13): Git Worktree + branch isolation

Part V, coming next, adds safety guarantees and observability to this system — the move from experiment to production.

## Summary

- Multiple agents working in the same directory leads to file conflicts
- Git Worktree creates an isolated working directory and branch for each task
- The control plane (`.tasks/`) manages goals; the execution plane (`.worktrees/`) manages environments
- WorktreeManager handles worktree creation, removal, and listing
- The event log records the full worktree lifecycle
- Worktree tools are Lead-exclusive — teammates work in the directories they are assigned
- Conflicts are resolved at Git merge time, not by overwriting each other during edits
