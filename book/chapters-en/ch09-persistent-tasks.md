<!-- Translated from: ch09-persistent-tasks.md -->

# Chapter 9: Persistent Tasks

> **Motto**: "Plans in memory vanish on restart — write them to disk."

> Take a moment to review your agent's task management capabilities. The TodoManager from Chapter 4 is an in-memory flat list — no dependency tracking, vulnerable to context compression (Chapter 6), and gone the instant you restart. For simple tasks, it does the job. But for truly complex projects — multi-step workflows with ordering constraints — you need something more powerful. This chapter introduces a file-level task graph (TaskGraph) that supports dependencies, persistent state, and cross-session survival.

> **Part III finale**: This is the last chapter of the DELEGATION phase. After this, your agent will have a complete delegation toolkit: sub-agents, background tasks, and a persistent task graph.

![Conceptual: Sub-agent delegation](images/ch09/fig-09-01-concept.png)

*Figure 9-1. Persistent tasks: write plans to disk so they survive restarts and sessions.*
## The Problem

Try this scenario:

```
You: 帮我重构这个项目：
     1) 先写测试（需要先读懂代码）
     2) 运行测试确认通过
     3) 重构代码（依赖步骤 1 的测试）
     4) 再次运行测试（依赖步骤 3 的重构）
     5) 更新文档（依赖步骤 3 的重构）
```

There are clear **dependencies** here: step 3 depends on steps 1 and 2, steps 4 and 5 both depend on step 3, but steps 4 and 5 are independent of each other (they can run in parallel).

How does TodoManager handle this?

```
todo: add "读懂代码" → pending
todo: add "写测试" → pending
todo: add "运行测试" → pending
todo: add "重构代码" → pending
todo: add "再次运行测试" → pending
todo: add "更新文档" → pending
```

Six independent pending items. The agent might rush off to "update documentation" — because it has no idea the docs depend on a refactor that has not happened yet. TodoManager has no concept of dependencies.

There is an even more serious problem: if context compression (Chapter 6) triggers mid-conversation, the agent's todo list only exists in the message history — it gets wiped out by compression. Or the user closes the terminal halfway through and reopens it the next day — everything resets to zero.

## The Solution

Introduce a file-level task graph — each task stored as a JSON file:

```
.tasks/
├── task_1.json  {"id": "task_1", "status": "completed", "description": "读懂代码", ...}
├── task_2.json  {"id": "task_2", "status": "completed", "blocked_by": [], ...}
├── task_3.json  {"id": "task_3", "status": "in_progress", "blocked_by": ["task_2"], ...}
├── task_4.json  {"id": "task_4", "status": "blocked", "blocked_by": ["task_3"], ...}
└── task_5.json  {"id": "task_5", "status": "blocked", "blocked_by": ["task_3"], ...}
```

This is a **directed acyclic graph (DAG)**:

```
task_1 (读懂代码) → task_2 (写测试) → task_3 (重构代码) → task_4 (再次测试)
                                                          → task_5 (更新文档)
```

Key properties:

1. **Persistence**: Written to disk — survives restarts, unaffected by compression
2. **Dependencies**: The `blocked_by` field defines prerequisite dependencies
3. **Automatic unblocking**: When task_3 completes, task_4 and task_5 automatically transition from `blocked` to `pending`
4. **Human-readable**: Plain JSON files that humans can inspect and edit directly

## 9.1 TaskGraph Implementation

```python
class TaskGraph:
    """文件级任务 DAG。每个任务一个 JSON 文件。"""

    def __init__(self, tasks_dir=TASKS_DIR):
        self._tasks_dir = tasks_dir
        os.makedirs(self._tasks_dir, exist_ok=True)
        self._counter = self._find_max_id()  # 从已有文件恢复计数器
```

`_find_max_id()` scans the `.tasks/` directory to find the highest ID number — this means that even after the agent restarts, newly created task IDs will not collide with existing ones.

**Creating a task**:

```python
def create(self, description, blocked_by=None, owner=""):
    self._counter += 1
    task_id = f"task_{self._counter}"

    # 验证依赖任务存在
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
        "created_at": "...",
        "updated_at": "...",
    }
    self._save(task)
    return task_id
```

Notice the automatic `status` logic: if `blocked_by` is provided, the task starts as `blocked`; otherwise it starts as `pending`.

**Status updates and automatic unblocking**:

```python
def update_status(self, task_id, status):
    task = self._load(task_id)
    # ... 验证 ...

    # 如果要启动一个被阻塞的任务，检查依赖是否都完成了
    if task["status"] == "blocked" and status == "in_progress":
        for dep_id in task["blocked_by"]:
            dep = self._load(dep_id)
            if dep and dep["status"] != "completed":
                return f"[error: 任务被 {dep_id} 阻塞]"

    task["status"] = status
    self._save(task)

    # 关键：完成时自动解除下游阻塞
    if status == "completed":
        self._unblock_downstream(task_id)
```

`_unblock_downstream` iterates over all tasks and finds downstream tasks that list the current task as a dependency. If all of a downstream task's dependencies are now completed, its status changes from `blocked` to `pending`.

This cascading unblock is the essence of the DAG — completing a single node can simultaneously unlock multiple downstream nodes.

## 9.2 Four Tools

TaskGraph exposes four CRUD tools:

| Tool | Function | Use Case |
|---|---|---|
| `task_create` | Create a task + define dependencies | Project planning phase |
| `task_update` | Update status + auto-unblock downstream | During execution |
| `task_list` | List all tasks (filterable by status) | Checking progress |
| `task_get` | View task details | Inspecting a specific task |

## 9.3 Integrating into the Agent

The `agent_loop` gains a `task_graph` parameter:

```python
def agent_loop(
    messages, todo_manager=None, context_manager=None,
    bg_manager=None, task_graph=None,  # NEW
):
    # ...
    if task_graph is not None:
        handlers.update(make_task_graph_handlers(task_graph))
```

The tool list expands with `*TASK_GRAPH_TOOLS`:

```python
TOOLS = [
    # ... 已有工具 ...
    *TASK_GRAPH_TOOLS,  # NEW: task_create, task_update, task_list, task_get
]
```

**An important design choice in the REPL**: the `clear` command does not reset the TaskGraph — because it is persistent. Just like typing `clear` in a terminal does not delete files from your disk:

```python
if user_input.lower() == "clear":
    messages.clear()
    todo_manager.__init__()
    context_manager.__init__()
    bg_manager.__init__()
    # 注意：task_graph 不重置——它是持久化的！
    print("[对话已清空（持久化任务图保留）]")
```

## 9.4 TodoManager vs TaskGraph

The two coexist, each with its own strengths:

| | TodoManager (todo) | TaskGraph (task_*) |
|---|---|---|
| **Storage** | In-memory | On-disk files |
| **Persistent** | No | Yes |
| **Dependencies** | None | Yes (blocked_by) |
| **Best for** | Simple tasks within a single session | Complex projects spanning sessions |
| **Context compression** | May be lost | Unaffected |
| **owner field** | None | Yes (groundwork for Part IV) |

When should you use which?

- **"Help me create a Python package"** -- `todo` is enough (5 steps, single session)
- **"Help me refactor the entire project"** -- `task_create` (multi-day effort, complex dependencies, needs persistence)

## 9.5 Try It Out

```bash
cd miniagent
python agent.py
```

```
工具: bash, read_file, write_file, edit_file, todo, load_skill, compact, task,
      bg_run, bg_check, task_create, task_update, task_list, task_get
```

Try creating tasks with dependencies:

```
You: 帮我规划一个 Web 项目：
     1) 设计数据库 schema
     2) 实现 API（依赖 schema）
     3) 写前端页面（依赖 API）
     4) 写测试（依赖 API）
     5) 部署（依赖前端和测试）
```

Watch how the agent uses `task_create` to establish the dependency relationships. Then:

```
You: 把 task_1 标记为完成
```

Watch `task_2` automatically transition from `blocked` to `pending`.

Exit and re-enter the REPL:

```bash
python agent.py
```

```
You: 列出所有任务
```

The tasks are still there. That is the value of persistence.

> **Try It Yourself**: Look at the JSON files in the `.tasks/` directory. Try manually editing a file's `status` field, then run `task_list` in the REPL — the agent sees your changes.

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +10 行（task_graph 参数、handler 注册）
├── todo.py             ← 保留（简单任务仍然有用）
├── skill_loader.py
├── context.py
├── subagent.py
├── background.py
├── tasks.py            ← NEW: 282 行（TaskGraph DAG、4 个 CRUD 工具）
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| Metric | Chapter 8 | Chapter 9 |
|------|-----------|-----------|
| Tool count | 10 | **14** (+task_create, +task_update, +task_list, +task_get) |
| Module count | 6 | **7** (+tasks.py) |
| Capabilities | Background execution | **+ Persistent task DAG** |
| Task management | In-memory list | **In-memory list + file-based DAG** |

**Part III complete.** Your agent now has a full "delegation" toolkit:

- **Sub-agents** (ch07): Delegate sub-tasks that require LLM reasoning
- **Background tasks** (ch08): Move slow operations that do not require reasoning into the background
- **Persistent task graph** (ch09): Manage complex projects with a DAG that survives across sessions

In the upcoming Part IV, you will build on these foundations to create a multi-agent collaboration system — giving sub-agents identities, letting them share a task graph, and communicating through a message bus. The TaskGraph's `owner` field will play a key role there.

## Summary

- TodoManager is an in-memory flat list — fine for simple tasks, but not persistent and has no dependency tracking
- TaskGraph stores tasks as `.tasks/{id}.json` files that survive restarts
- The `blocked_by` field defines DAG dependencies; completing a task automatically unblocks downstream tasks
- `_find_max_id()` recovers the counter from disk, ensuring IDs never collide
- The two task systems coexist — `todo` for lightweight management, `task_*` for heavyweight project management
- The `clear` command preserves the TaskGraph — persistent data should not be wiped by a session operation

The next chapter begins Part IV: COLLABORATION — giving your sub-agents identities and roles, building a true multi-agent team.
