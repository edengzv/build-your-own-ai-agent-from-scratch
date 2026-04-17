# Chapter 8: 后台任务

> **Motto**: "慢操作放后台，Agent 继续思考"

> 上一章你让 Agent 学会了委托——把子任务交给子智能体处理。但子智能体是同步的——父 Agent 必须等子 Agent 完成才能继续。如果任务是"运行测试套件"（2 分钟）或"安装依赖"（30 秒），整个 Agent 就卡住了。本章你将引入后台任务管理器，让耗时操作在后台线程中异步执行，Agent 继续处理其他事务。

## The Problem

让 Agent 做一个典型的开发工作流：

```
You: 帮我做以下事情：
     1) 运行 pytest 测试套件
     2) 同时检查代码风格 (pylint)
     3) 两个都完成后告诉我结果
```

用目前的 `bash` 工具：

```
[Tool: bash] pytest tests/ -v       → 等待 90 秒...
[Tool: bash] pylint src/ --score=y  → 再等待 45 秒...
```

总计 135 秒——Agent 完全空闲地等待。它不能同时做两件事，因为 `bash` 工具是同步阻塞的：`subprocess.run()` 会一直等到命令完成。

更糟的情况：Agent 在等测试的时候，它本可以先去做代码检查的准备工作、生成报告模板、甚至处理用户的下一个问题。但它被困在了 `subprocess.run()` 里。

## The Solution

引入后台任务管理器——将 `subprocess.run()` 放进独立的线程：

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

关键机制：

1. **`bg_run` 工具**：启动后台进程，立即返回 task_id
2. **daemon 线程**：每个后台进程在独立线程中执行
3. **通知队列**：进程完成后，结果放入线程安全的通知队列
4. **自动注入**：每次 LLM 调用前，检查通知队列，将完成的结果注入到消息中

## 8.1 BackgroundManager 设计

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

`BackgroundManager` 管理所有后台任务：

```python
class BackgroundManager:
    def __init__(self):
        self._tasks: dict[str, BgTask] = {}
        self._notifications: list[str] = []
        self._lock = threading.Lock()
        self._counter = 0
```

三个关键方法：

- `start(command, timeout)` → 启动后台命令，返回 task_id
- `check(task_id)` → 查询任务状态
- `drain()` → 获取并清空所有待处理的通知

## 8.2 线程安全

后台任务在独立线程中运行，与主线程共享 `_tasks` 和 `_notifications`。必须用锁保护：

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

`daemon=True` 很重要——如果用户按 Ctrl+C 退出 REPL，后台线程会自动终止，不会挂起进程。

## 8.3 通知机制

后台线程完成后，将结果放入通知队列：

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

在 `agent_loop` 中，每次调用 LLM 之前检查通知：

```python
# 在 agent_loop 的 while True 中：
if bg_manager is not None:
    notifications = bg_manager.drain()
    for note in notifications:
        print(f"  [Background] 任务完成通知")
        messages.append({"role": "user", "content": note})
```

`drain()` 是原子操作——获取并清空，确保每个通知只被处理一次。

## 8.4 工具定义

两个工具配合使用：

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

`bg_check` 的 `required` 是空的——不传 task_id 时列出所有任务，传了则检查特定任务。

## 8.5 集成到 Agent

`agent_loop` 增加 `bg_manager` 参数，三处改动：

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

通知注入的位置很重要——必须在 LLM 调用**之前**。这样 Agent 能在下一轮看到结果并做出反应。

## 8.6 后台 vs 子智能体：何时用哪个

| | 后台任务 (bg_run) | 子智能体 (task) |
|---|---|---|
| **适用场景** | 不需要 LLM 推理的操作 | 需要 LLM 推理的子问题 |
| **例子** | 运行测试、安装依赖、编译 | 分析代码、写报告、调研 |
| **执行方式** | subprocess 在线程中 | 独立的 agent_loop |
| **返回结果** | 命令输出 | LLM 生成的文本 |
| **是否异步** | 是（立即返回） | 否（同步阻塞） |

简单的判断标准：**需要 LLM 思考吗？** 需要 → task，不需要 → bg_run。

## 8.7 试一试

```bash
cd miniagent
python agent.py
```

```
工具: bash, read_file, write_file, edit_file, todo, load_skill, compact, task, bg_run, bg_check
```

测试后台执行：

```
You: 在后台运行 "sleep 5 && echo done"，然后告诉我当前时间
```

Agent 应该会：
1. 用 `bg_run` 启动后台命令
2. 立即用 `bash` 执行 `date` 获取当前时间
3. 5 秒后，后台任务完成，Agent 收到通知

> **Try It Yourself**：同时启动两个后台任务——`bg_run "sleep 3 && echo task1"` 和 `bg_run "sleep 5 && echo task2"`。观察它们的完成通知是按完成顺序到达的，而不是按启动顺序。

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +15 行（bg_manager 参数、drain 注入、bg handlers）
├── todo.py
├── skill_loader.py
├── context.py
├── subagent.py
├── background.py       ← NEW: 170 行（BackgroundManager、BG_RUN/BG_CHECK 工具）
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| 指标 | Chapter 7 | Chapter 8 |
|------|-----------|-----------|
| 工具数 | 8 | **10** (+bg_run, +bg_check) |
| 模块数 | 5 | **6** (+background.py) |
| 能力 | 委托子任务 | **+后台异步执行** |
| 并发模型 | 同步 | **同步 + 异步** |

**核心架构演进**：

```
Ch1-6: 单线程、同步
Ch7:   + 子 Agent（同步委托）
Ch8:   + 后台线程（异步执行）← you are here
```

Agent 现在有了两种"分工"方式：需要 LLM 思考的子任务委托给子智能体，不需要思考的耗时操作放到后台。下一章，我们将解决最后一个分工问题——任务的持久化和依赖管理。

## Summary

- 同步阻塞让 Agent 在等待慢操作时完全空闲——浪费时间
- `BackgroundManager` 用 daemon 线程执行后台命令，主循环继续运行
- 通知队列（`drain()`）是线程安全的——后台线程写入，主线程读取，不会冲突
- 通知在 LLM 调用前注入 messages，Agent 自然地在下一轮看到结果
- 后台任务适合不需要 LLM 推理的操作（测试、构建、安装）
- 子智能体适合需要 LLM 推理的子问题（分析、生成、调研）

下一章是 Part III 的最后一章：持久化任务图。你将把内存中的 TodoManager 升级为文件级的 DAG 任务系统，支持依赖关系和持久化——重启不丢失，压缩不遗忘。
