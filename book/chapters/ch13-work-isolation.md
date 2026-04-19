# Chapter 13: 工作隔离

> **Motto**: "各自在自己的目录工作，互不干扰"

> 上一章让队友学会了自主认领任务。但有个严重问题被忽略了——多个队友在同一个目录工作。如果两个队友同时编辑 `app.py`，一个的修改会被另一个覆盖。本章引入 Git Worktree 绑定任务的机制，每个队友在自己的独立工作目录中操作。

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

reviewer 读到的是版本 A，但 developer 已经将文件改为版本 B。reviewer 的编辑操作基于过时的版本——`old_string` 已经不存在了。

更糟糕的场景：两个队友同时用 `write_file` 写同一个文件——后写的直接覆盖先写的，数据丢失。

这是**多 Agent 文件冲突**——和人类开发者不用分支直接在 main 上工作是一样的问题。

## The Solution

引入**两个层面**的分离：

```
控制面（不变）          执行面（隔离）
.tasks/                .worktrees/
├── task_1.json        ├── task_1/     ← reviewer 的工作目录
├── task_2.json        ├── task_2/     ← developer 的工作目录
└── task_3.json        └── events.jsonl
```

- **控制面** (`.tasks/`)：存储目标和状态——做什么、谁在做、做到哪了
- **执行面** (`.worktrees/`)：提供隔离的工作环境——每个任务一个 Git Worktree

Git Worktree 是 Git 原生的特性：从同一个仓库创建多个工作目录，每个有自己的分支，但共享同一个 `.git` 历史。比复制整个目录高效得多。

## 13.1 WorktreeManager

```python
class WorktreeManager:
    def __init__(self, base_dir=""):
        self._base_dir = base_dir or os.getcwd()
        os.makedirs(WORKTREES_DIR, exist_ok=True)
```

**创建 Worktree**：

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

每个 worktree 是一个完整的工作目录——有自己的文件树、自己的分支、可以独立 commit。但它们共享同一个 Git 对象库（`.git/`），所以创建速度非常快。

**移除 Worktree**：

```python
def remove(self, task_id, keep=False):
    subprocess.run(
        ["git", "worktree", "remove", wt_path, "--force"],
        cwd=self._base_dir, ...
    )
```

`keep=True` 保留分支（可以稍后合并），`keep=False` 完全清理。

## 13.2 事件日志

每个 worktree 的生命周期事件记录在 `.worktrees/events.jsonl`：

```json
{"type": "created", "task_id": "task_1", "timestamp": "...", "branch": "task-task_1"}
{"type": "removed", "task_id": "task_1", "timestamp": "..."}
```

状态机：`absent → created → removed | kept`

这提供了审计追踪——你可以回顾任何时间点有哪些 worktree 在活动。

## 13.3 三个工具

| 工具 | 功能 | 使用者 |
|---|---|---|
| `worktree_create` | 为任务创建隔离工作目录 | Lead |
| `worktree_remove` | 任务完成后移除 worktree | Lead |
| `worktree_list` | 列出所有活跃的 worktree | Lead |

这三个工具是 Lead 专属的——队友不需要自己管理 worktree，Lead 在分配任务时创建，完成后清理。

## 13.4 集成到 Agent

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

`agent_loop` 增加 `wt_manager` 参数：

```python
def agent_loop(messages, ..., wt_manager=None):
    if wt_manager is not None:
        handlers.update(make_worktree_handlers(wt_manager))
```

## 13.5 工作流

完整的隔离工作流：

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

每个队友在自己的分支上工作，完成后通过 Git merge 合并。冲突在合并时才处理——而不是在编辑时互相覆盖。

## 13.6 试一试

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

试试创建隔离工作环境：

```
You: 创建两个任务，为每个任务创建 worktree，然后列出所有 worktree
```

```
You: 查看 .worktrees/ 目录结构
```

> **Try It Yourself**：进入 `.worktrees/task_1/` 目录，用 `git branch` 查看当前分支。你会看到它在 `task-task_1` 分支上，和主目录完全隔离。

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

| 指标 | Chapter 12 | Chapter 13 |
|------|------------|------------|
| 工具数 | 21 | **24** (+worktree_create, +worktree_remove, +worktree_list) |
| 模块数 | 10 | **11** (+worktree.py) |
| 能力 | 自主认领 | **+Git Worktree 隔离** |
| 文件安全 | 可能冲突 | **分支隔离** |

**Part IV 完成**。你的多智能体系统现在具备完整的协作能力：

- **团队** (ch10)：持久化队友 + 邮箱通信
- **协议** (ch11)：安全关闭 + 方案审批
- **自主** (ch12)：任务扫描 + 自动认领
- **隔离** (ch13)：Git Worktree + 分支隔离

接下来的 Part V 将为这个系统添加安全保障和可观测性——从实验走向生产。

## Summary

- 多个 Agent 在同一目录工作会导致文件冲突
- Git Worktree 为每个任务创建隔离的工作目录和分支
- 控制面 (`.tasks/`) 管理目标，执行面 (`.worktrees/`) 管理环境
- WorktreeManager 处理 worktree 的创建、移除和列表
- 事件日志记录 worktree 的完整生命周期
- worktree 工具是 Lead 专属——队友在被分配的目录中工作
- 冲突在 Git merge 时处理，而不是在编辑时互相覆盖
