<!-- Translated from: ch08-background-tasks.md -->

# Chapter 8: Background Tasks

> **Motto**: "Put slow operations in the background — let the agent keep thinking."

> In the previous chapter you taught the agent to delegate — handing sub-tasks to sub-agents. But sub-agents are synchronous: the parent agent must wait for the child to finish before it can continue. If the task is "run the test suite" (2 minutes) or "install dependencies" (30 seconds), the entire agent freezes. In this chapter you introduce a background task manager that runs time-consuming operations asynchronously in background threads while the agent carries on with other work.

![Conceptual: Extensible modular architecture](images/ch08/fig-08-01-concept.png)

*Figure 8-1. Background tasks: slow operations run in parallel while the agent keeps thinking.*
## The Problem

Have the agent perform a typical development workflow:

```
You: 帮我做以下事情：
     1) 运行 pytest 测试套件
     2) 同时检查代码风格 (pylint)
     3) 两个都完成后告诉我结果
```

With the current `bash` tool:

```
[Tool: bash] pytest tests/ -v       → 等待 90 秒...
[Tool: bash] pylint src/ --score=y  → 再等待 45 秒...
```

Total: 135 seconds — the agent sitting completely idle the whole time. It cannot do two things at once because the `bash` tool is synchronous and blocking: `subprocess.run()` waits until the command finishes.

It gets worse. While waiting for the tests, the agent could have been preparing the code-check report template, or even handling the user's next question. But it is stuck inside `subprocess.run()`.

## The Solution

Introduce a background task manager — move `subprocess.run()` into its own thread:

```
┌──────────────────────────────────────┐
│            Agent Loop                │
│                                      │
│  [bg_run] pytest tests/              │
│      → bg_1 已启动，继续...           │
│                                      │
│  [bg_run] pylint src/                │
│      → bg_2 已启动，继续...           │
│                                      │
│  (Agent 继续做其他事情)               │
│                                      │
│  ... 90 秒后 ...                     │
│                                      │
│  <background-result bg_1>            │  ← 自动注入
│  <background-result bg_2>            │  ← 自动注入
│                                      │
│  Agent: 两个任务都完成了...            │
└──────────────────────────────────────┘
```

The key mechanisms:

1. **`bg_run` tool**: starts a background process and immediately returns a task_id
2. **Daemon thread**: each background process runs in its own thread
3. **Notification queue**: when a process finishes, its result is placed in a thread-safe notification queue
4. **Auto-injection**: before each LLM call, the queue is checked and completed results are injected into the messages

## 8.1 BackgroundManager Design

```python
@dataclass
class BgTask:
    """一个后台任务的状态。"""
    task_id: str
    command: str
    status: str = "running"  # running | completed | failed | timed_out
    output: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
```

`BackgroundManager` manages all background tasks:

```python
class BackgroundManager:
    def __init__(self):
        self._tasks: dict[str, BgTask] = {}
        self._notifications: list[str] = []
        self._lock = threading.Lock()
        self._counter = 0
```

Three key methods:

- `start(command, timeout)` — starts a background command, returns a task_id
- `check(task_id)` — queries task status
- `drain()` — retrieves and clears all pending notifications

## 8.2 Thread Safety

Background tasks run in separate threads and share `_tasks` and `_notifications` with the main thread. Locks are essential:

```python
def start(self, command: str, timeout: int = 120) -> str:
    with self._lock:
        self._counter += 1
        task_id = f"bg_{self._counter}"

    task = BgTask(task_id=task_id, command=command)
    with self._lock:
        self._tasks[task_id] = task

    thread = threading.Thread(
        target=self._run_command,
        args=(task, timeout),
        daemon=True,  # 主进程退出时自动清理
    )
    thread.start()
    return task_id
```

`daemon=True` is important — if the user hits Ctrl+C to exit the REPL, daemon threads are automatically terminated instead of hanging the process.

## 8.3 The Notification Mechanism

When a background thread finishes, it places the result into the notification queue:

```python
def _run_command(self, task: BgTask, timeout: int) -> None:
    try:
        result = subprocess.run(
            task.command, shell=True,
            capture_output=True, text=True, timeout=timeout,
        )
        # ... 设置 status 和 output ...
        with self._lock:
            self._notifications.append(
                f"<background-result task_id='{task.task_id}' "
                f"status='{status}' elapsed='{elapsed:.1f}s'>\n"
                f"命令: {task.command}\n输出:\n{task.output[:2000]}\n"
                f"</background-result>"
            )
    except subprocess.TimeoutExpired:
        # ... 超时处理 ...
```

In `agent_loop`, notifications are checked before every LLM call:

```python
# 在 agent_loop 的 while True 中：
if bg_manager is not None:
    notifications = bg_manager.drain()
    for note in notifications:
        print(f"  [Background] 任务完成通知")
        messages.append({"role": "user", "content": note})
```

`drain()` is atomic — it retrieves and clears in one step, ensuring each notification is processed exactly once.

## 8.4 Tool Definitions

Two tools work together:

```python
BG_RUN_TOOL = {
    "name": "bg_run",
    "description": "在后台启动一个命令。立即返回任务 ID，不等待完成。"
                   "适用于耗时操作：测试、安装依赖、构建项目等。",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的命令"},
            "timeout": {"type": "integer", "description": "超时时间（秒），默认 120"},
        },
        "required": ["command"],
    },
}

BG_CHECK_TOOL = {
    "name": "bg_check",
    "description": "检查后台任务的状态和输出。",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "任务 ID"},
        },
        "required": [],
    },
}
```

Notice that `bg_check` has an empty `required` array — when no task_id is passed it lists all tasks; when one is passed it checks that specific task.

## 8.5 Integrating into the Agent

`agent_loop` gains a `bg_manager` parameter with three changes:

```python
def agent_loop(
    messages, todo_manager=None, context_manager=None,
    bg_manager=None,  # NEW
):
    # 1. 注册 bg handlers
    if bg_manager is not None:
        handlers.update(make_bg_handlers(bg_manager))

    while True:
        # 2. 注入后台任务通知（在 LLM 调用前）
        if bg_manager is not None:
            notifications = bg_manager.drain()
            for note in notifications:
                messages.append({"role": "user", "content": note})

        # 3. 正常的 LLM 调用和工具执行
        response = client.messages.create(...)
```

The placement of notification injection matters — it must happen **before** the LLM call. That way the agent sees completed results in the next turn and can react to them.

## 8.6 Background Tasks vs. Sub-Agents: When to Use Which

| | Background Tasks (bg_run) | Sub-Agents (task) |
|---|---|---|
| **Best for** | Operations that do not require LLM reasoning | Sub-problems that require LLM reasoning |
| **Examples** | Running tests, installing dependencies, compiling | Analyzing code, writing reports, research |
| **Execution** | subprocess in a thread | Independent agent_loop |
| **Returns** | Command output | LLM-generated text |
| **Async?** | Yes (returns immediately) | No (synchronous, blocking) |

A simple rule of thumb: **Does it need the LLM to think?** Yes — use `task`. No — use `bg_run`.

## 8.7 Try It Yourself

```bash
cd miniagent
python agent.py
```

```
工具: bash, read_file, write_file, edit_file, todo, load_skill, compact, task, bg_run, bg_check
```

Test background execution:

```
You: 在后台运行 "sleep 5 && echo done"，然后告诉我当前时间
```

The agent should:
1. Use `bg_run` to start the background command
2. Immediately use `bash` to run `date` and get the current time
3. Five seconds later, the background task completes and the agent receives the notification

> **Try It Yourself**: Start two background tasks at the same time — `bg_run "sleep 3 && echo task1"` and `bg_run "sleep 5 && echo task2"`. Notice that their completion notifications arrive in order of completion, not in order of submission.

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +15 行（bg_manager 参数、drain 注入、bg handlers）
├── todo.py
├── skill_loader.py
├── context.py
├── subagent.py
├── background.py       ← NEW: 190 行（BackgroundManager、BG_RUN/BG_CHECK 工具）
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| Metric | Chapter 7 | Chapter 8 |
|--------|-----------|-----------|
| Tools | 8 | **10** (+bg_run, +bg_check) |
| Modules | 5 | **6** (+background.py) |
| Capabilities | Delegate sub-tasks | **+ async background execution** |
| Concurrency model | Synchronous | **Synchronous + asynchronous** |

**Core architecture evolution**:

```
Ch1-6: 单线程、同步
Ch7:   + 子 Agent（同步委托）
Ch8:   + 后台线程（异步执行）← you are here
```

The agent now has two ways to divide work: sub-tasks that need LLM reasoning are delegated to sub-agents, and time-consuming operations that do not need reasoning go to the background. In the next chapter, we tackle the final piece of the division-of-labor puzzle — task persistence and dependency management.

## Summary

- Synchronous blocking leaves the agent completely idle while waiting for slow operations — a waste of time
- `BackgroundManager` uses daemon threads to run background commands while the main loop keeps running
- The notification queue (`drain()`) is thread-safe — background threads write, the main thread reads, no conflicts
- Notifications are injected into messages before the LLM call, so the agent naturally sees results in the next turn
- Background tasks are best for operations that do not need LLM reasoning (tests, builds, installs)
- Sub-agents are best for sub-problems that need LLM reasoning (analysis, generation, research)

The next chapter is the final chapter of Part III: the persistent task graph. You will upgrade the in-memory TodoManager into a file-backed DAG task system with dependency tracking and persistence — restarts do not lose progress, and context compaction does not lose tasks.
