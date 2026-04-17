# Chapter 13: 工作隔离

> **Motto**: "各自在自己的目录工作，互不干扰"

> 到这里，你的多智能体系统有一个致命问题：所有 Agent 都在同一个工作目录中操作。当两个队友同时编辑 `app.py`，一个的修改会被另一个覆盖。本章引入 Git Worktree 隔离——每个任务在自己的独立工作目录中执行，通过分支合并回主线。

## The Problem

场景复现：

```
reviewer: [Tool: edit_file] app.py  (修改第 50 行)
tester:   [Tool: write_file] app.py (重写整个文件，覆盖 reviewer 的修改)
```

两个 Agent 在同一个文件上"打架"。更糟糕的是，它们可能在不同文件中创建互相矛盾的修改——reviewer 重命名了一个函数，tester 还在用旧名字写测试。

这不是 Agent 的问题，是架构的问题。在软件工程中，这个问题早就有解决方案：**分支**。每个人在自己的分支上工作，完成后合并。

## 13.1 控制面 vs 执行面

引入一个重要的概念分离：

```
控制面 (Control Plane)         执行面 (Execution Plane)
┌─────────────────────┐       ┌──────────────────────────┐
│ .tasks/             │       │ .worktrees/              │
│   task_001.json     │───────│   task_001/              │
│   task_002.json     │───────│   task_002/              │
│                     │       │   (每个是完整的工作目录)   │
└─────────────────────┘       └──────────────────────────┘
```

- **控制面**（`.tasks/`）：存储任务的元数据——描述、状态、依赖、Owner。轻量级 JSON 文件。
- **执行面**（`.worktrees/`）：存储任务的工作环境——完整的代码副本。通过 Git Worktree 实现。

控制面是"地图"，执行面是"战场"。Agent 在控制面上规划，在执行面上执行。

## 13.2 Git Worktree 入门

Git Worktree 允许一个仓库同时有多个工作目录，每个绑定到不同的分支：

```bash
# 创建 worktree：基于当前分支创建一个新的工作目录
git worktree add .worktrees/task_001 -b task_001

# 列出所有 worktree
git worktree list

# 删除 worktree
git worktree remove .worktrees/task_001
```

每个 worktree 是完整的工作目录——有自己的文件、自己的暂存区、自己的 HEAD。但它们**共享一个 .git 仓库**，所以创建非常快（不需要 clone）。

为什么比复制目录好？
1. **共享 .git**：不浪费磁盘空间
2. **自动跟踪分支**：合并冲突可以用标准 git merge 解决
3. **原子操作**：创建和删除是 git 管理的

## 13.3 WorktreeManager

```python
class WorktreeManager:
    def __init__(self, base_dir=""):
        self._base = base_dir or os.path.join(os.getcwd(), ".worktrees")
        os.makedirs(self._base, exist_ok=True)
        self._events: list[dict] = []
```

**创建 worktree**：

```python
def create(self, task_id, branch="") -> str:
    branch = branch or f"task/{task_id}"
    wt_path = os.path.join(self._base, task_id)
    if os.path.exists(wt_path):
        return f"[error: worktree {task_id} 已存在]"

    result = subprocess.run(
        ["git", "worktree", "add", wt_path, "-b", branch],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return f"[error: {result.stderr.strip()}]"

    self._record_event(task_id, "created", branch=branch)
    return f"已创建 worktree: {wt_path} (分支: {branch})"
```

**删除 worktree**：

```python
def remove(self, task_id, keep=False) -> str:
    wt_path = os.path.join(self._base, task_id)
    if not os.path.exists(wt_path):
        return f"[error: worktree {task_id} 不存在]"

    if keep:
        self._record_event(task_id, "kept")
        return f"保留 worktree {task_id} 以供检查"

    result = subprocess.run(
        ["git", "worktree", "remove", wt_path, "--force"],
        capture_output=True, text=True
    )
    self._record_event(task_id, "removed")
    return f"已删除 worktree: {task_id}"
```

`keep=True` 选项允许保留 worktree 以供人类检查——有时 Agent 完成的工作需要人类审查后再决定是否合并。

## 13.4 事件流

每个 worktree 操作都记录为事件：

```python
def _record_event(self, task_id, action, **extra):
    event = {
        "task_id": task_id,
        "action": action,  # created, removed, kept
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        **extra,
    }
    self._events.append(event)
```

状态机：`absent → created → removed | kept`

通过 `get_events()` 可以查看完整的 worktree 生命周期：

```python
def get_events(self, task_id="") -> str:
    filtered = self._events
    if task_id:
        filtered = [e for e in filtered if e["task_id"] == task_id]
    if not filtered:
        return "没有 worktree 事件"
    return "\n".join(json.dumps(e, ensure_ascii=False) for e in filtered)
```

## 13.5 三个工具

| 工具 | 功能 |
|------|------|
| `worktree_create` | 为任务创建隔离的工作目录 |
| `worktree_remove` | 任务完成后清理工作目录 |
| `worktree_list` | 列出当前所有 worktree |

```python
WORKTREE_TOOLS = [CREATE_WT_TOOL, REMOVE_WT_TOOL, LIST_WT_TOOL]
```

## 13.6 集成到 Agent

`agent.py` 的变更：

```python
from worktree import WorktreeManager, WORKTREE_TOOLS, make_worktree_handlers

# 工具列表添加
TOOLS = [..., *WORKTREE_TOOLS]

# _PARENT_ONLY 添加
_PARENT_ONLY = {
    ...,
    "worktree_create", "worktree_remove", "worktree_list",
}

# agent_loop 增加参数
def agent_loop(
    ...,
    wt_manager: WorktreeManager | None = None,
):
    ...
    if wt_manager is not None:
        handlers.update(make_worktree_handlers(wt_manager))
```

Worktree 工具放在 `_PARENT_ONLY` 中——只有 Lead 可以创建和管理 worktree。队友在分配到的 worktree 中工作，但不能创建新的。

## 13.7 试一试

```bash
cd miniagent
python agent.py
```

```
You: 为 task_001 创建一个工作目录

  [Tool: worktree_create] task_001

You: 列出当前的工作目录

  [Tool: worktree_list]
```

```
You: 任务完成了，清理工作目录

  [Tool: worktree_remove] task_001
```

> **Try It Yourself**：手动进入 `.worktrees/task_001/` 目录，修改一些文件，然后回到主目录看看——两个工作目录是完全独立的。试试 `git log` 对比两边的提交历史。

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +15 行（worktree 导入、参数、handler）
├── worktree.py         ← NEW: 184 行（WorktreeManager、事件流、3 个工具）
├── autonomous.py
├── protocols.py
├── team.py
├── tasks.py
├── background.py
├── context.py
├── subagent.py
├── skill_loader.py
└── todo.py
```

| 指标 | Chapter 12 | Chapter 13 |
|------|-----------|------------|
| 工具数 | 26 | **29** (+worktree_create, +worktree_remove, +worktree_list) |
| 模块数 | 10 | **11** (+worktree.py) |
| 能力 | 自主认领 | **+工作目录隔离** |
| 隔离方式 | 无 | **Git Worktree** |

## Summary

- 多个 Agent 在同一目录工作会导致文件冲突
- 控制面（`.tasks/`）管理目标和状态，执行面（`.worktrees/`）提供隔离环境
- Git Worktree 允许同一仓库有多个工作目录，共享 `.git`，创建快速
- WorktreeManager 封装了 worktree 的创建、删除、列表和事件记录
- 事件流记录 worktree 的完整生命周期：absent → created → removed | kept
- Worktree 工具是 Lead 专属——队友在分配的 worktree 中工作但不创建新的
- `keep=True` 选项允许保留完成的 worktree 以供人类审查
