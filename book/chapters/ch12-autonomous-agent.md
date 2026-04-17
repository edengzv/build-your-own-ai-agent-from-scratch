# Chapter 12: 自主智能体

> **Motto**: "队友主动扫描任务板，认领自己能做的"

> 到目前为止，队友都是被动的——Lead 必须通过 `send` 手动分配每一个任务。如果 Lead 创建了一个包含 20 个任务的任务图，它需要逐个发送给合适的队友。Lead 变成了"任务调度器"，而不是"策略决策者"。本章让队友变得自主：在空闲时扫描任务板，找到自己能做的未认领任务，主动认领并执行。

## The Problem

```
You: 创建 20 个代码审查任务

Agent: [Tool: task_create] 审查 module_1.py
Agent: [Tool: task_create] 审查 module_2.py
...
Agent: [Tool: send] → reviewer：审查 module_1.py
Agent: [Tool: send] → reviewer：审查 module_2.py
...
```

Lead 花了大量时间分配任务，而不是思考策略。如果有 3 个 reviewer 队友，Lead 还得负责负载均衡——把任务均匀分给每个人。

理想的模式应该是：Lead 创建任务，队友自动认领。就像真实团队中的看板（Kanban）——Lead 把卡片放到"待做"列，团队成员自己去拿。

## 12.1 IDLE/WORK 循环

每个自主队友运行一个两阶段循环：

```
┌──────────────────────────────┐
│  IDLE                         │
│  ├─ 检查邮箱（有消息？→ WORK） │
│  ├─ 扫描任务板（有未认领？→ WORK）│
│  ├─ 检查关闭请求              │
│  └─ 等待 poll_interval（5秒） │
│      超时计数 → idle_timeout  │
│      → 自动关闭               │
└──────────────────────────────┘
          ↕
┌──────────────────────────────┐
│  WORK                         │
│  ├─ 执行认领的任务            │
│  ├─ 完成 → 标记任务完成       │
│  ├─ 重置 idle 计时器          │
│  └─ 回到 IDLE                │
└──────────────────────────────┘
```

关键参数：
- `poll_interval = 5.0`：空闲时每 5 秒检查一次
- `idle_timeout = 60.0`：连续空闲 60 秒后自动关闭

自动关闭防止队友无限空转——如果所有任务都做完了，队友就自己退出。

## 12.2 AutonomousLoop 类

```python
class AutonomousLoop:
    def __init__(self, name, role, idle_timeout=60.0, poll_interval=5.0):
        self.name = name
        self.role = role
        self.idle_timeout = idle_timeout
        self.poll_interval = poll_interval
        self._idle_since = time.time()
        self._shutdown = False
```

核心方法——**扫描并认领任务**：

```python
def check_and_claim(self) -> dict | None:
    tasks_dir = os.path.join(os.getcwd(), ".tasks")
    if not os.path.isdir(tasks_dir):
        return None

    for fname in sorted(os.listdir(tasks_dir)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(tasks_dir, fname)) as f:
            task = json.load(f)

        if task.get("status") != "pending":
            continue
        if task.get("owner"):
            continue  # 已有人认领

        # 认领！
        task["owner"] = self.name
        task["status"] = "in_progress"
        with open(os.path.join(tasks_dir, fname), "w") as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        return task

    return None
```

注意扫描逻辑：
1. 只看 `.tasks/` 目录中的 JSON 文件
2. 只认领 `status == "pending"` 且没有 `owner` 的任务
3. 认领是"读-改-写"操作——不是真正的原子操作

> **并发风险**：两个队友可能同时认领同一个任务。在生产环境中，这需要文件锁或数据库事务。在我们的教学场景中，这种冲突很少发生，我们暂时接受这个限制。

## 12.3 三个自主工具

| 工具 | 功能 | 使用者 |
|------|------|--------|
| `scan_tasks` | 扫描任务板中的待认领任务 | 队友 |
| `claim_task` | 认领指定任务 | 队友 |
| `complete_my_task` | 标记任务为完成 | 队友 |

```python
AUTONOMOUS_TOOLS = [CLAIM_TASK_TOOL, COMPLETE_TASK_TOOL, SCAN_TASKS_TOOL]
```

工厂函数绑定 `AutonomousLoop` 实例：

```python
def make_autonomous_handlers(auto_loop):
    def handle_scan_tasks():
        task = auto_loop.check_and_claim()
        if task is None:
            return "没有可认领的任务"
        return f"已认领任务: {task['id']} — {task.get('description', '')}"

    def handle_claim_task(task_id):
        # 认领指定 ID 的任务
        ...

    def handle_complete(task_id, result=""):
        ok = auto_loop.mark_complete(task_id, result)
        if ok:
            auto_loop.reset_timer()
            return f"任务 {task_id} 已完成"
        return f"[error: 无法完成任务 {task_id}]"

    return {
        "scan_tasks": handle_scan_tasks,
        "claim_task": handle_claim_task,
        "complete_my_task": handle_complete,
    }
```

`handle_complete` 调用 `reset_timer()`——完成任务后重置空闲计时器，延长队友的存活时间。

## 12.4 队友的工具集演化

到本章为止，工具集的分层结构已经很清晰：

```
TOOLS (所有工具)
  └→ _PARENT_ONLY 排除 → CHILD_TOOLS (子智能体工具)
     └→ + TEAMMATE_PROTOCOL_TOOLS → (协议工具)
     └→ + AUTONOMOUS_TOOLS → TEAMMATE_TOOLS (队友完整工具集)
```

```python
TEAMMATE_TOOLS = CHILD_TOOLS + TEAMMATE_PROTOCOL_TOOLS + AUTONOMOUS_TOOLS
```

在 `agent.py` 中，spawn 队友时组装 handler：

```python
def handle_spawn(name, role):
    teammate_handlers = dict(child_handlers)
    teammate_handlers.update(make_teammate_protocol_handlers(name))
    auto_loop = AutonomousLoop(name=name, role=role)
    teammate_handlers.update(make_autonomous_handlers(auto_loop))
    return team_manager.spawn(
        ...,
        tools=TEAMMATE_TOOLS,
        tool_handlers=teammate_handlers,
    )
```

每个队友有自己的 `AutonomousLoop` 实例——不同队友的空闲计时器和认领记录是独立的。

## 12.5 自主的边界

完全自主可能很危险——如果队友认领了一个它不具备能力的任务怎么办？现阶段我们采用简单策略：

1. **任何待认领的任务都可以被认领**：不做能力匹配
2. **Lead 可以通过 `task_create` 的 description 引导**：描述中写明"适合 reviewer 角色"
3. **队友做不了可以标记失败**：用 `complete_my_task` 并在 result 中说明

更成熟的方案（在第 16 章讨论）包括：任务标签匹配、角色能力声明、自动回退机制。

## 12.6 试一试

```bash
cd miniagent
python agent.py
```

```
You: 创建一个 reviewer 队友，然后创建 3 个审查任务，观察它自动认领

  [Tool: spawn] reviewer (代码审查员)
  [Tool: task_create] 审查 todo.py
  [Tool: task_create] 审查 context.py
  [Tool: task_create] 审查 subagent.py
```

观察：reviewer 会在 IDLE 循环中发现这些任务，自动调用 `scan_tasks` 认领并执行。

```
You: 查看任务状态

  [Tool: task_list] (所有任务)
  // 可以看到任务的 owner 字段被设置为 "reviewer"
```

> **Try It Yourself**：创建 2 个不同角色的队友和 5 个任务，观察它们如何分配。试试在没有任务时，队友是否会在 60 秒后自动关闭。

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +15 行（autonomous 导入、TEAMMATE_TOOLS 定义、spawn 集成）
├── autonomous.py       ← NEW: 196 行（AutonomousLoop、IDLE/WORK 循环、3 个工具）
├── protocols.py
├── team.py
├── tasks.py
├── background.py
├── context.py
├── subagent.py
├── skill_loader.py
└── todo.py
```

| 指标 | Chapter 11 | Chapter 12 |
|------|-----------|------------|
| 工具数 | 23 | **26** (+scan_tasks, +claim_task, +complete_my_task) |
| 模块数 | 9 | **10** (+autonomous.py) |
| 能力 | 结构化协议 | **+自主任务认领** |
| 队友模式 | 被动等待 | **+主动扫描** |

## Summary

- 被动队友需要 Lead 手动分配每个任务，Lead 沦为调度器
- AutonomousLoop 实现 IDLE/WORK 两阶段循环：扫描 → 认领 → 执行 → 完成 → 回到扫描
- 任务认领通过读取 `.tasks/` 目录中的 pending 任务并设置 owner
- 三个自主工具：scan_tasks（扫描）、claim_task（认领）、complete_my_task（完成）
- TEAMMATE_TOOLS = CHILD_TOOLS + TEAMMATE_PROTOCOL_TOOLS + AUTONOMOUS_TOOLS
- idle_timeout 机制防止队友无限空转，没有任务时自动关闭
- 每个队友的 AutonomousLoop 实例独立，空闲计时器和认领记录互不影响
