<!-- Translated from: ch04-task-planning.md -->

# Chapter 4: Task Planning

> **Motto**: "An agent without a plan just wanders aimlessly."

> Give an agent a multi-step task — "create a Python package with setup.py, a README, and tests" — and it fumbles around, skipping steps, repeating work, losing track of the goal. In this chapter, you introduce a TodoManager that lets the agent break complex tasks into steps and track progress. This is the critical leap from "can do work" to "can think about work."

![Conceptual: An autonomous planning loop](images/ch04/fig-04-01-concept.png)

*Figure 4-1. The planning loop: think, act, observe, repeat — turning chaos into ordered steps.*
## The Problem

Fire up the REPL and give the agent a complex task:

```
You: 帮我创建一个叫 mylib 的 Python 包，要求：
     1) 有 setup.py
     2) 有 README.md 说明用法
     3) 有一个 mylib/__init__.py 导出版本号
     4) 有 tests/test_basic.py 基本测试
     5) 运行测试确认通过
```

Without planning ability, the agent might do this: create setup.py → forget README → jump straight to running tests → tests fail because there is no `__init__.py` → go back and add it → run tests again → remember README still is not written...

It is not that the agent cannot do the work — it just does not know where it is in the process. When humans tackle complex tasks, they make a checklist and tick items off. An agent needs one too.

## The Solution

Introduce a new module `todo.py`, containing a `TodoManager` class and a `todo` tool.

```
┌──────────────────────────────────┐
│          agent_loop()            │
│  ┌────────────┐                  │
│  │    LLM     │                  │
│  └─────┬──────┘                  │
│        ↓                         │
│  ┌────────────────────────────┐  │
│  │     TOOL_HANDLERS { }     │  │
│  │  bash | read | write | ed │  │
│  │  ┌──────────────────────┐ │  │
│  │  │     todo (NEW)       │ │  │
│  │  │  add | update | list │ │  │
│  │  └──────────────────────┘ │  │
│  └────────────────────────────┘  │
│        ↑                         │
│  ┌────────────────┐              │
│  │  TodoManager   │ ← NEW       │
│  │  ○ #1 pending  │              │
│  │  ◉ #2 in_prog  │              │
│  │  ✓ #3 done     │              │
│  └────────────────┘              │
└──────────────────────────────────┘
```

## Designing TodoManager

`TodoManager` is an in-memory task list manager. Create `todo.py`:

```python
# todo.py — NEW file

VALID_STATUSES = ("pending", "in_progress", "completed")

class TodoManager:
    """内存中的任务列表管理器。"""

    def __init__(self):
        self.todos: list[dict] = []
        self._rounds_since_update = 0  # 用于提醒机制

    def add(self, content: str) -> str:
        """添加一个新的待办事项。"""
        todo = {
            "id": len(self.todos) + 1,
            "content": content,
            "status": "pending",
        }
        self.todos.append(todo)
        self._rounds_since_update = 0
        return f"已添加任务 #{todo['id']}: {content}"

    def update_status(self, todo_id: int, status: str) -> str:
        """更新任务状态。"""
        if status not in VALID_STATUSES:
            return f"[error: 无效状态 '{status}']"

        todo = self._find(todo_id)
        if todo is None:
            return f"[error: 任务 #{todo_id} 不存在]"

        # 约束：同一时间只能有一个 in_progress
        if status == "in_progress":
            current_wip = [t for t in self.todos if t["status"] == "in_progress"]
            if current_wip and current_wip[0]["id"] != todo_id:
                return (
                    f"[error: 任务 #{current_wip[0]['id']} 正在进行中。"
                    f"请先完成它，再开始新任务]"
                )

        old_status = todo["status"]
        todo["status"] = status
        self._rounds_since_update = 0
        return f"任务 #{todo_id}: {old_status} → {status}"

    def list_todos(self) -> str:
        """列出所有任务及其状态。"""
        if not self.todos:
            return "任务列表为空。"

        lines = ["任务列表:"]
        status_icons = {"pending": "○", "in_progress": "◉", "completed": "✓"}
        for t in self.todos:
            icon = status_icons.get(t["status"], "?")
            lines.append(f"  {icon} #{t['id']} [{t['status']}] {t['content']}")

        total = len(self.todos)
        done = sum(1 for t in self.todos if t["status"] == "completed")
        lines.append(f"\n进度: {done}/{total} 已完成")
        return "\n".join(lines)
```

The data structure is simple: a list of dictionaries, each with an `id`, `content`, and `status`.

Key design decisions:

**Only one `in_progress` at a time.** Why? Because the agent is single-threaded — it can only do one thing at a time. If you allow multiple `in_progress` items, the agent will jump between tasks, which actually reduces efficiency. This constraint forces the agent to complete tasks linearly.

**Return strings instead of raising exceptions.** Consistent with the tool design principle from Chapter 2 — error messages are meant for the LLM to read, understand, and correct.

## Implementing the todo Tool

The todo tool is a "multi-action" tool — a single tool supporting three operations: `add`, `update_status`, and `list`:

```python
TODO_TOOL = {
    "name": "todo",
    "description": (
        "管理任务列表。用于规划多步骤任务、追踪进度。"
        "在开始复杂任务前，先用 add 拆解步骤；执行时用 update_status 更新状态。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "update_status", "list"],
                "description": "操作类型",
            },
            "content": {"type": "string", "description": "任务内容 (add 时必填)"},
            "todo_id": {"type": "integer", "description": "任务 ID (update_status 时必填)"},
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed"],
                "description": "目标状态 (update_status 时必填)",
            },
        },
        "required": ["action"],
    },
}
```

> **Note**: Why not split add, update, and list into three separate tools? Because they are conceptually one capability — task management. The LLM finds it easier to understand "one tool called todo" than "three tools called todo_add, todo_update, and todo_list." As a general rule, closely related operations within the same domain should be combined; unrelated operations should be kept separate.

The handler function is created via a `make_todo_handler` factory function, bound to a specific TodoManager instance:

```python
def make_todo_handler(manager: TodoManager):
    def handle_todo(action: str, **kwargs) -> str:
        if action == "add":
            return manager.add(kwargs.get("content", ""))
        elif action == "update_status":
            return manager.update_status(int(kwargs.get("todo_id", 0)),
                                         kwargs.get("status", ""))
        elif action == "list":
            return manager.list_todos()
        else:
            return f"[error: 未知操作 '{action}']"
    return handle_todo
```

## The Reminder Mechanism

Just because the todo tool exists does not mean the LLM will proactively use it. It might break the task into steps, then bury itself in execution, forgetting to update status.

The solution is a "nag reminder" — if the agent goes 3 consecutive rounds without calling the todo tool, a reminder message is automatically injected:

```python
# TodoManager 中
def tick(self) -> str | None:
    """每轮调用一次。连续多轮未更新则返回提醒。"""
    self._rounds_since_update += 1
    if self._rounds_since_update >= 3 and self.todos:
        pending = [t for t in self.todos if t["status"] != "completed"]
        if pending:
            return (
                "<reminder>你有未完成的任务。请用 todo 工具更新进度，"
                "或标记当前任务为 completed。</reminder>"
            )
    return None
```

In `agent_loop`, call `tick()` at the start of each round:

```python
# agent_loop 中 — NEW
if todo_manager is not None:
    reminder = todo_manager.tick()
    if reminder:
        messages.append({"role": "user", "content": reminder})
```

This is a "guide, not enforce" design. The reminder is wrapped in `<reminder>` tags so the LLM understands it is a system hint rather than user input. If the todo genuinely does not need updating, the LLM can ignore it.

## Integrating into the Agent

The changes to `agent.py` are minimal:

```python
from todo import TodoManager, TODO_TOOL, make_todo_handler  # NEW

# TOOLS 列表末尾
TOOLS = [
    # ... 原有 4 个工具 ...
    TODO_TOOL,  # NEW
]

# agent_loop 签名变化
def agent_loop(messages: list, todo_manager: TodoManager | None = None):  # CHANGED
    handlers = { ... }
    if todo_manager is not None:  # NEW
        handlers["todo"] = make_todo_handler(todo_manager)
    # ... 循环不变 ...

# repl 中创建 TodoManager
def repl():
    messages = []
    todo_manager = TodoManager()  # NEW
    # ...
    agent_loop(messages, todo_manager)  # CHANGED
```

The core loop's structure remains unchanged. All we added is one tool and one reminder injection point.

## Planning vs. Execution

With the todo tool in place, the agent has two working modes:

**Plan-then-Execute**: List all steps first, then execute them one by one. Best for tasks with clear goals.

```
todo add "创建 mylib/ 目录结构"
todo add "编写 setup.py"
todo add "编写 README.md"
todo add "编写 tests/test_basic.py"
todo add "运行测试"
--- 规划完成，开始执行 ---
todo update_status 1 in_progress
[执行] mkdir mylib, touch __init__.py
todo update_status 1 completed
todo update_status 2 in_progress
...
```

**Interleaved**: Plan and execute at the same time, dynamically adjusting the plan based on execution results. Best for exploratory tasks.

Each mode has its strengths. The system prompt's instruction to "break complex tasks into steps using the todo tool before starting" nudges the agent toward Plan-then-Execute, but does not force it.

> **Tip**: If you want the agent to follow Plan-then-Execute more strictly, you can add "before marking the first task as in_progress, make sure all steps are listed" to the system prompt. But overly rigid rules reduce flexibility — some tasks simply cannot be fully planned before execution begins.

## Seeing It in Action

```bash
python miniagent/agent.py "创建一个 mylib 包，要有 setup.py、README、__init__.py 和测试"
```

```
You: 创建一个 mylib 包，要有 setup.py、README、__init__.py 和测试
  [Tool: todo] add 创建 mylib 目录结构
  已添加任务 #1: 创建 mylib 目录结构
  [Tool: todo] add 编写 setup.py
  已添加任务 #2: 编写 setup.py
  [Tool: todo] add 编写 README.md
  已添加任务 #3: 编写 README.md
  [Tool: todo] add 编写 mylib/__init__.py
  已添加任务 #4: 编写 mylib/__init__.py
  [Tool: todo] add 编写并运行 tests/test_basic.py
  已添加任务 #5: 编写并运行 tests/test_basic.py
  [Tool: todo] update_status 1 in_progress
  任务 #1: pending → in_progress
  [Tool: bash] mkdir -p mylib tests
  (no output)
  [Tool: todo] update_status 1 completed
  任务 #1: in_progress → completed
  [Tool: todo] update_status 2 in_progress
  任务 #2: pending → in_progress
  [Tool: write_file] setup.py
  已写入 setup.py (245 字符)
  ...
```

Notice the agent's behavior: it plans 5 steps first, then executes them in order, marking each `in_progress` when it starts and `completed` when it finishes. Orderly and trackable.

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| No task management; complex tasks rely on "memory" alone | TodoManager tracks every step |
| Agent may skip steps, repeat work, or lose track of the goal | Clear pending → in_progress → completed transitions |
| 4 tools | 5 tools (+todo) |
| 1 file (agent.py) | 2 files (agent.py + todo.py) |

**Cumulative capability**: Your MiniAgent can now execute commands, read and write files, hold multi-turn conversations, plan multi-step tasks, and track progress.

## Try It Yourself

1. **Verify**: Give the agent a task with 5 or more steps. Observe whether it plans before it executes. During execution, have it run `todo list` and confirm the statuses are correct.

2. **Extend**: Add a `remove` operation to TodoManager that lets the agent delete tasks that are no longer needed. Update `handle_todo` and the `TODO_TOOL` schema accordingly.

3. **Explore**: In the REPL, go 5 consecutive rounds without using the todo tool and observe whether the reminder mechanism fires. Think about this: what if the agent ignores the reminder? Are there stronger enforcement mechanisms? (Hint: you could inject the todo list into the system prompt, but that comes with a token cost.)

## Summary

- **TodoManager** provides three operations — add / update_status / list — for managing a task list
- The **single in_progress constraint** forces the agent to work linearly, preventing it from jumping between tasks
- The **reminder mechanism** (nag reminder) injects a prompt when the agent goes 3 consecutive rounds without updating the todo
- The **factory function pattern** `make_todo_handler(manager)` binds a tool handler to a specific state instance
- Plan-then-Execute suits tasks with clear goals; Interleaved suits exploratory tasks
- This chapter introduced the first **standalone module** `todo.py` — every new capability going forward will be its own module

In the next chapter, you will let the agent load domain knowledge on demand, rather than cramming everything into the system prompt.

## Further Reading

- Yao, S., et al. (2023). "ReAct: Synergizing Reasoning and Acting in Language Models." *ICLR 2023* — Theoretical foundation for the interleaved reasoning-action pattern
- Wei, J., et al. (2022). "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." *NeurIPS 2022* — The classic method for getting LLMs to think step by step
