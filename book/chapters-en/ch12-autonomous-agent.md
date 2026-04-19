<!-- Translated from: ch12-autonomous-agent.md -->

# Chapter 12: Autonomous Agents

> **Motto**: "Teammates proactively scan the task board and claim the work they can do."

> Up to this point, teammates only work when explicitly told to — Lead has to manually assign every task via `send`. Lead is busy "messaging the reviewer," "messaging the tester," turning into a message relay instead of a strategic thinker. This chapter makes teammates autonomous — they scan the task board (the `.tasks/` directory) when idle, claim tasks they are capable of, and automatically shut down after a timeout.

![Conceptual: Parallel background processing](images/ch12/fig-12-01-concept.png)

*Figure 12-1. Autonomous agents: teammates that scan for work and act on their own initiative.*
## The Problem

Scenario: you use `task_create` to lay out a 10-step project plan, then spawn two teammates — a reviewer and a tester.

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

Lead becomes a manual scheduler for the task queue. Ten tasks require ten messages, and Lead has to wait for each one to finish before sending the next. This is not "leading" — this is "message hauling."

The ideal: Lead creates the task graph, spawns teammates, and then teammates go find work on the task board themselves.

## The Solution

Introduce the **IDLE/WORK autonomous loop**:

```
队友的生命周期：
  spawn → IDLE → 发现任务 → claim → WORK → 完成 → IDLE → ...
                 ↓ (60s 没活干)
              auto-SHUTDOWN
```

Three new tools for teammates:

| Tool | Purpose |
|---|---|
| `scan_tasks` | Scan `.tasks/` for claimable tasks |
| `claim_task` | Atomically claim a pending task |
| `complete_my_task` | Mark your own task as completed |

## 12.1 Scanning for Claimable Tasks

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

Two conditions: `status == "pending"` **and** `owner` is empty. This ensures:
- Blocked tasks are not claimed (their dependencies have not been completed yet)
- Tasks already claimed by another teammate are not claimed again

## 12.2 Atomic Claiming

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

"Atomic" is a simplification here — we are not using file locks but relying on a "check-then-set" pattern. In a single-machine, multi-thread environment, the probability of two teammates claiming the same task simultaneously is very low. Even if a conflict occurs, one claim simply fails (returns False) without corrupting data.

In a production system, you would use database transactions or distributed locks for true atomicity. But for learning purposes, this simplified version demonstrates the core idea.

## 12.3 The AutonomousLoop Wrapper

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

Key design decisions:
- **Auto-shutdown on timeout**: After 60 seconds of idleness, `should_shutdown()` returns True. This prevents useless teammates from occupying resources forever.
- **Activity timer reset**: Claiming a task, completing a task, and receiving a mailbox message all reset the timer.

## 12.4 Task Completion and Cascading Unblock

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

Notice `_unblock_downstream` — this is consistent with the TaskGraph logic from Chapter 9. When a task completes, its downstream tasks transition from `blocked` to `pending`, and other idle teammates can then discover these newly unlocked tasks on their next scan.

This creates an elegant **pipeline effect**:
1. Teammate A completes task_1
2. task_2 automatically transitions from blocked to pending
3. Teammate B discovers task_2 on its next scan, claims it, and begins working
4. Lead does not need to intervene at all

## 12.5 Integrating into the Agent

The teammate's toolset gains three new autonomous tools:

```python
TEAMMATE_TOOLS = CHILD_TOOLS + TEAMMATE_PROTOCOL_TOOLS + AUTONOMOUS_TOOLS
```

The AutonomousLoop is injected at spawn time:

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

Each teammate gets its own independent `AutonomousLoop` instance — its own timeout timer, its own activity tracker.

## 12.6 Balancing Passive and Autonomous Modes

Teammates now have two ways to receive tasks:

| Mode | Trigger | Scenario |
|---|---|---|
| **Passive** | Lead assigns via `send` | Tasks requiring specific instructions |
| **Autonomous** | Teammate discovers via `scan_tasks` | Standard tasks already on the task board |

The two modes coexist. Lead can:
1. Create a task graph and let teammates claim tasks automatically (autonomous mode)
2. Send a message directly and have teammates handle it immediately (passive mode)

This is not either-or — the same teammate can respond to mailbox messages and scan the task board at the same time.

## 12.7 Try It Out

```bash
cd miniagent
python agent.py
```

Try the autonomous workflow:

```
You: 帮我规划一个 Web 项目：
     1) 设计 API（无依赖）
     2) 写前端（依赖 API）
     3) 写测试（依赖 API）
     4) 部署（依赖前端和测试）
     然后创建两个队友来自动完成这些任务
```

Watch how the agent:
1. Uses `task_create` to build a dependency-aware task graph
2. Uses `spawn` to create two teammates
3. Teammates automatically `scan_tasks`, `claim_task`, execute, then `complete_my_task`
4. Completing a task automatically unblocks downstream tasks, and other teammates claim them

> **Try It Yourself**: Watch the `owner` field change in the JSON files inside the `.tasks/` directory. Different tasks get claimed by different teammates.

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

| Metric | Chapter 11 | Chapter 12 |
|------|------------|------------|
| 工具数 | 21 | **21**（Lead 不变；队友 +3：scan_tasks, claim_task, complete_my_task）|
| 模块数 | 9 | **10** (+autonomous.py) |
| 能力 | 结构化协议 | **+自主任务认领** |
| 队友行为 | 被动等待 | **被动 + 自主扫描** |

Notice that Lead's tool count stays the same — the autonomous tools are for teammates only. Lead does not need `scan_tasks`; it directs through `task_create` and `send`.

The next chapter tackles a classic problem in multi-agent collaboration: file conflicts. What happens when two teammates edit the same file at the same time?

## Summary

- Passive teammates require Lead to manually assign every task, turning Lead into a "message hauler"
- Autonomous teammates proactively scan the `.tasks/` directory, claiming tasks that are pending and have no owner
- AutonomousLoop encapsulates autonomous behavior: scanning, claiming, and auto-shutdown on timeout
- `claim_task` uses a "check-then-set" pattern for simplified atomic claiming
- Completing a task triggers a cascading unblock, producing a pipeline effect
- Passive and autonomous modes coexist — Lead can flexibly choose between them
- Auto-shutdown after 60 seconds of idleness prevents resource waste
