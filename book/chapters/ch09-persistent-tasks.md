# Chapter 9: 持久化任务

> **Motto**: "内存里的计划重启就丢了，写到磁盘上"

> 回顾一下你的 Agent 的任务管理能力。第 4 章的 TodoManager 是一个内存中的扁平列表——没有依赖关系，上下文压缩后可能丢失，重启就没了。对于简单任务，它足够了。但对于真正复杂的项目——有前后依赖的多步骤工作流——你需要更强大的东西。本章将引入文件级任务图（TaskGraph），支持依赖关系、状态持久化和跨会话保持。

> **Part III 终章**：这是 DELEGATION 阶段的最后一章。完成后，你的 Agent 将拥有完整的分工能力：子智能体、后台任务、持久化任务图。

## The Problem

试试这个场景：

```
You: 帮我重构这个项目：
     1) 先写测试（需要先读懂代码）
     2) 运行测试确认通过
     3) 重构代码（依赖步骤 1 的测试）
     4) 再次运行测试（依赖步骤 3 的重构）
     5) 更新文档（依赖步骤 3 的重构）
```

这里有清晰的**依赖关系**：步骤 3 依赖步骤 1 和 2，步骤 4 和 5 都依赖步骤 3，但步骤 4 和 5 之间互不依赖（可以并行）。

用 TodoManager 怎么处理？

```
todo: add "读懂代码" → pending
todo: add "写测试" → pending
todo: add "运行测试" → pending
todo: add "重构代码" → pending
todo: add "再次运行测试" → pending
todo: add "更新文档" → pending
```

六个独立的 pending 项目。Agent 可能先跑去"更新文档"——因为它不知道文档依赖于还没做的重构。TodoManager 没有依赖关系的概念。

更严重的问题：如果对话进行到一半触发了上下文压缩（第 6 章），Agent 的 todo 列表只存在于消息历史中——压缩后就丢了。或者用户中途关闭了终端，明天重新打开——一切归零。

## The Solution

引入文件级任务图——每个任务存为一个 JSON 文件：

```
.tasks/
├── task_1.json  {"id": "task_1", "status": "completed", "description": "读懂代码", ...}
├── task_2.json  {"id": "task_2", "status": "completed", "blocked_by": [], ...}
├── task_3.json  {"id": "task_3", "status": "in_progress", "blocked_by": ["task_2"], ...}
├── task_4.json  {"id": "task_4", "status": "blocked", "blocked_by": ["task_3"], ...}
└── task_5.json  {"id": "task_5", "status": "blocked", "blocked_by": ["task_3"], ...}
```

这是一个**有向无环图（DAG）**：

```
task_1 (读懂代码) → task_2 (写测试) → task_3 (重构代码) → task_4 (再次测试)
                                                          → task_5 (更新文档)
```

关键特性：

1. **持久化**：写在磁盘上，重启不丢失，压缩不影响
2. **依赖关系**：`blocked_by` 字段定义前置依赖
3. **自动解除阻塞**：完成 task_3 时，自动将 task_4 和 task_5 从 `blocked` 变为 `pending`
4. **可读性**：JSON 文件，人类可以直接查看和编辑

## 9.1 TaskGraph 实现

```python
class TaskGraph:
    """文件级任务 DAG。每个任务一个 JSON 文件。"""

    def __init__(self, tasks_dir=TASKS_DIR):
        self._tasks_dir = tasks_dir
        os.makedirs(self._tasks_dir, exist_ok=True)
        self._counter = self._find_max_id()  # 从已有文件恢复计数器
```

`_find_max_id()` 扫描 `.tasks/` 目录找到最大的 ID 编号——这意味着即使 Agent 重启，新建的任务 ID 也不会与旧任务冲突。

**创建任务**：

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

注意 `status` 的自动判断：有 `blocked_by` 就是 `blocked`，没有就是 `pending`。

**状态更新与自动解除阻塞**：

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

`_unblock_downstream` 遍历所有任务，找到以当前任务为依赖的下游任务。如果下游任务的所有依赖都已完成，将其状态从 `blocked` 改为 `pending`。

这个级联解除是 DAG 的精髓——完成一个节点可能同时解锁多个下游节点。

## 9.2 四个工具

TaskGraph 提供四个 CRUD 工具：

| 工具 | 功能 | 场景 |
|---|---|---|
| `task_create` | 创建任务 + 定义依赖 | 项目规划阶段 |
| `task_update` | 更新状态 + 自动解除阻塞 | 执行过程中 |
| `task_list` | 列出所有任务（可按状态过滤） | 查看进度 |
| `task_get` | 查看任务详情 | 了解具体任务 |

## 9.3 集成到 Agent

`agent_loop` 增加 `task_graph` 参数：

```python
def agent_loop(
    messages, todo_manager=None, context_manager=None,
    bg_manager=None, task_graph=None,  # NEW
):
    # ...
    if task_graph is not None:
        handlers.update(make_task_graph_handlers(task_graph))
```

工具列表用 `*TASK_GRAPH_TOOLS` 展开：

```python
TOOLS = [
    # ... 已有工具 ...
    *TASK_GRAPH_TOOLS,  # NEW: task_create, task_update, task_list, task_get
]
```

**REPL 中的一个重要设计**：`clear` 命令不会重置 TaskGraph——因为它是持久化的。就像你在终端里输入 `clear` 不会删除磁盘上的文件一样：

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

两者共存，各有用武之地：

| | TodoManager (todo) | TaskGraph (task_*) |
|---|---|---|
| **存储** | 内存 | 磁盘文件 |
| **持久化** | 否 | 是 |
| **依赖关系** | 无 | 有（blocked_by） |
| **适用场景** | 单次会话的简单任务 | 跨会话的复杂项目 |
| **上下文压缩** | 可能丢失 | 不受影响 |
| **owner 字段** | 无 | 有（为 Part IV 铺垫） |

何时用哪个？

- **"帮我创建一个 Python 包"** → `todo` 足够（5 步，单次会话完成）
- **"帮我重构整个项目"** → `task_create`（多天工作，有复杂依赖，需要持久化）

## 9.5 试一试

```bash
cd miniagent
python agent.py
```

```
工具: bash, read_file, write_file, edit_file, todo, load_skill, compact, task,
      bg_run, bg_check, task_create, task_update, task_list, task_get
```

试试创建有依赖的任务：

```
You: 帮我规划一个 Web 项目：
     1) 设计数据库 schema
     2) 实现 API（依赖 schema）
     3) 写前端页面（依赖 API）
     4) 写测试（依赖 API）
     5) 部署（依赖前端和测试）
```

观察 Agent 如何用 `task_create` 建立依赖关系。然后：

```
You: 把 task_1 标记为完成
```

观察 `task_2` 如何自动从 `blocked` 变为 `pending`。

退出后重新进入 REPL：

```bash
python agent.py
```

```
You: 列出所有任务
```

任务还在！这就是持久化的价值。

> **Try It Yourself**：查看 `.tasks/` 目录中的 JSON 文件。试着手动编辑一个文件的 `status` 字段，然后在 REPL 中用 `task_list` 查看——Agent 能看到你的修改。

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +10 行（task_graph 参数、handler 注册）
├── todo.py             ← 保留（简单任务仍然有用）
├── skill_loader.py
├── context.py
├── subagent.py
├── background.py
├── tasks.py            ← NEW: 240 行（TaskGraph DAG、4 个 CRUD 工具）
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| 指标 | Chapter 8 | Chapter 9 |
|------|-----------|-----------|
| 工具数 | 10 | **14** (+task_create, +task_update, +task_list, +task_get) |
| 模块数 | 6 | **7** (+tasks.py) |
| 能力 | 后台执行 | **+持久化任务 DAG** |
| 任务管理 | 内存列表 | **内存列表 + 文件 DAG** |

**Part III 完成**。你的 Agent 现在拥有完整的"分工"能力：

- **子智能体** (ch07)：将需要 LLM 推理的子任务委托出去
- **后台任务** (ch08)：将不需要推理的慢操作放到后台
- **持久化任务图** (ch09)：用 DAG 管理复杂项目，跨会话保持

接下来的 Part IV，你将在这些基础上构建多智能体协作系统——给子智能体身份、让它们共享任务图、通过消息总线通信。TaskGraph 的 `owner` 字段将在那里发挥关键作用。

## Summary

- TodoManager 是内存中的扁平列表，适合简单任务，但不持久、无依赖
- TaskGraph 将任务存为 `.tasks/{id}.json` 文件，重启不丢失
- `blocked_by` 字段定义 DAG 依赖关系，完成任务时自动解除下游阻塞
- `_find_max_id()` 从磁盘恢复计数器，确保 ID 不冲突
- 两套任务系统共存——todo 做轻量级管理，task_* 做重量级项目管理
- `clear` 命令保留 TaskGraph——持久化数据不应该被会话操作删除

下一章开始 Part IV: COLLABORATION——给你的子智能体身份和角色，构建一个真正的多智能体团队。
