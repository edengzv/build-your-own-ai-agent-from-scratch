# Chapter 12: 自主智能体

> **Motto**: "队友主动扫描任务板，认领自己能做的"

> 到目前为止，队友只在被明确指示时才工作——Lead 必须通过 `send` 手动分配每一个任务。Lead 忙于"给 reviewer 发消息"、"给 tester 发消息"，变成了一个消息转发器，而不是一个战略思考者。本章让队友变得自主——在空闲时扫描任务板（`.tasks/` 目录），认领自己能做的任务，超时后自动关闭。

![Conceptual: Parallel background processing](images/ch12/fig-12-01-concept.png)

*Figure 12-1. Autonomous agents: teammates that scan for work and act on their own initiative.*
## The Problem

场景：你用 `task_create` 创建了一个 10 步的项目计划，然后 spawn 了两个队友——reviewer 和 tester。

```
You: 创建项目计划（10 个任务），启动 reviewer 和 tester

Agent: [Tool: task_create] ... (创建了 10 个任务)
       [Tool: spawn] reviewer (代码审查员)
       [Tool: spawn] tester (测试工程师)
       
       现在我需要分配任务...
       [Tool: send] → reviewer：请做 task_1
       
       (等 reviewer 完成...)
       
       [Tool: send] → tester：请做 task_2
       
       (等 tester 完成...)
       
       [Tool: send] → reviewer：请做 task_3
       ...
```

Lead 变成了任务队列的手动调度器。10 个任务要发 10 条消息，还要等每个完成后再发下一个。这不是"领导"，这是"消息搬运工"。

理想情况：Lead 创建任务图，spawn 队友，然后队友自己去任务板上找活干。

## The Solution

引入 **IDLE/WORK 自主循环**：

```
队友的生命周期：
  spawn → IDLE → 发现任务 → claim → WORK → 完成 → IDLE → ...
                 ↓ (60s 没活干)
              auto-SHUTDOWN
```

三个新工具给队友使用：

| 工具 | 功能 |
|---|---|
| `scan_tasks` | 扫描 `.tasks/` 中可认领的任务 |
| `claim_task` | 原子性认领一个 pending 任务 |
| `complete_my_task` | 标记自己的任务为完成 |

## 12.1 扫描可认领的任务

```python
def scan_claimable_tasks(role=""):
    claimable = []
    for fname in sorted(os.listdir(TASKS_DIR)):
        task = json.load(open(path))
        # 只认领 pending 且未被 own 的任务
        if task.get("status") == "pending" and not task.get("owner"):
            claimable.append(task)
    return claimable
```

两个条件：`status == "pending"` **且** `owner` 为空。这确保：
- blocked 的任务不会被认领（依赖还没完成）
- 已被其他队友认领的任务不会重复认领

## 12.2 原子性认领

```python
def claim_task(task_id, owner):
    task = json.load(open(path))
    # 检查是否仍然可认领
    if task.get("status") != "pending" or task.get("owner"):
        return False  # 已被其他人认领
    task["owner"] = owner
    task["status"] = "in_progress"
    json.dump(task, open(path, "w"))
    return True
```

"原子性"在这里是一个简化——我们没有用文件锁，而是依赖"检查-然后-设置"模式。在单机多线程环境下，两个队友同时认领同一个任务的概率很低，即使发生冲突，也只是一个认领失败（返回 False），不会导致数据损坏。

在生产系统中，你会用数据库事务或分布式锁来保证真正的原子性。但对于学习目的，这个简化版本展示了核心思想。

## 12.3 AutonomousLoop 封装

```python
class AutonomousLoop:
    def __init__(self, name, role, idle_timeout=60.0, poll_interval=5.0):
        self.name = name
        self.role = role
        self.idle_timeout = idle_timeout
        self._last_activity = time.time()

    def check_and_claim(self):
        """检查可认领任务，返回认领到的或 None。"""
        tasks = scan_claimable_tasks(self.role)
        for task in tasks:
            if claim_task(task["id"], self.name):
                self._last_activity = time.time()
                return task
        return None

    def should_shutdown(self):
        """60 秒没活干就自动关闭。"""
        return (time.time() - self._last_activity) > self.idle_timeout
```

关键设计：
- **超时自动关闭**：空闲 60 秒后 `should_shutdown()` 返回 True。这防止了无用的队友永远占用资源。
- **活动计时重置**：认领任务、完成任务、收到邮箱消息都会重置计时器。

## 12.4 任务完成与级联解除

```python
def complete_task(task_id, owner, result=""):
    task = json.load(open(path))
    if task.get("owner") != owner:
        return False  # 只有 owner 能完成自己的任务
    task["status"] = "completed"
    task["result"] = result
    json.dump(task, open(path, "w"))
    _unblock_downstream(task_id)  # 自动解除下游阻塞
    return True
```

注意 `_unblock_downstream`——这和 Chapter 9 的 TaskGraph 逻辑一致。当一个任务完成时，它的下游任务从 `blocked` 变为 `pending`，其他空闲的队友就能扫描到这些新解锁的任务。

这创造了一个优美的**流水线效应**：
1. 队友 A 完成 task_1
2. task_2 自动从 blocked → pending
3. 队友 B 在下次扫描时发现 task_2，认领并开始工作
4. Lead 不需要干预任何事

## 12.5 集成到 Agent

队友的工具集新增三个自主工具：

```python
TEAMMATE_TOOLS = CHILD_TOOLS + TEAMMATE_PROTOCOL_TOOLS + AUTONOMOUS_TOOLS
```

spawn 时注入 AutonomousLoop：

```python
def handle_spawn(name, role):
    teammate_handlers = dict(child_handlers)
    teammate_handlers.update(make_teammate_protocol_handlers(name))
    auto_loop = AutonomousLoop(name=name, role=role)  # NEW
    teammate_handlers.update(make_autonomous_handlers(auto_loop))  # NEW
    return team_manager.spawn(
        name=name, role=role,
        tools=TEAMMATE_TOOLS,
        tool_handlers=teammate_handlers,
        ...
    )
```

每个队友有自己独立的 `AutonomousLoop` 实例——独立的超时计时器、独立的活动追踪。

## 12.6 被动 vs 自主的平衡

队友现在有两种获取任务的方式：

| 方式 | 触发 | 场景 |
|---|---|---|
| **被动** | Lead 通过 `send` 分配 | 需要特定指示的任务 |
| **自主** | 队友通过 `scan_tasks` 发现 | 已在任务板上的标准任务 |

两种方式共存。Lead 可以：
1. 创建任务图 → 队友自动认领（自主模式）
2. 直接 send 消息 → 队友立即处理（被动模式）

这不是非此即彼——同一个队友可以同时响应邮箱消息和扫描任务板。

## 12.7 试一试

```bash
cd miniagent
python agent.py
```

试试自主工作流：

```
You: 帮我规划一个 Web 项目：
     1) 设计 API（无依赖）
     2) 写前端（依赖 API）
     3) 写测试（依赖 API）
     4) 部署（依赖前端和测试）
     然后创建两个队友来自动完成这些任务
```

观察 Agent 如何：
1. 用 `task_create` 建立有依赖的任务图
2. 用 `spawn` 创建两个队友
3. 队友自动 `scan_tasks` → `claim_task` → 执行 → `complete_my_task`
4. 完成任务自动解锁下游，其他队友认领

> **Try It Yourself**：观察 `.tasks/` 目录中 JSON 文件的 `owner` 字段变化。不同的任务被不同的队友认领。

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +10 行（autonomous 导入、spawn 注入 AutonomousLoop）
├── todo.py
├── skill_loader.py
├── context.py
├── subagent.py
├── background.py
├── tasks.py
├── team.py
├── protocols.py
├── autonomous.py       ← NEW: 196 行（AutonomousLoop、scan/claim/complete、3 个工具）
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| 指标 | Chapter 11 | Chapter 12 |
|------|------------|------------|
| 工具数 | 21 | **21**（Lead 不变；队友 +3：scan_tasks, claim_task, complete_my_task）|
| 模块数 | 9 | **10** (+autonomous.py) |
| 能力 | 结构化协议 | **+自主任务认领** |
| 队友行为 | 被动等待 | **被动 + 自主扫描** |

注意 Lead 的工具数没变——自主工具只给队友使用。Lead 不需要 `scan_tasks`，它通过 `task_create` 和 `send` 来指挥。

下一章将解决一个多 Agent 协作的经典问题：文件冲突。两个队友同时编辑同一个文件会怎样？

## Summary

- 被动队友需要 Lead 手动分配每个任务，Lead 变成"消息搬运工"
- 自主队友主动扫描 `.tasks/` 目录，认领 pending 且无 owner 的任务
- AutonomousLoop 封装了自主行为：扫描、认领、超时关闭
- `claim_task` 使用"检查-然后-设置"模式实现简化的原子性认领
- 完成任务触发级联解除阻塞，形成流水线效应
- 被动和自主两种模式共存，Lead 可灵活选择
- 空闲 60 秒自动关闭，防止资源浪费
