# Chapter 4: 任务规划

> **Motto**: "没有计划的 Agent 只会漫无目的地游荡"

> 给 Agent 一个多步骤任务——"创建一个 Python 包，包含 setup.py、README 和测试"——它会东一下西一下，跳步、重复、忘记目标。本章你将引入 TodoManager，让 Agent 能将复杂任务拆解为步骤并追踪进度。这是 Agent 从"能干活"到"会思考"的关键一步。

![Conceptual: An autonomous planning loop](images/ch04/fig-04-01-concept.png)

*Figure 4-1. The planning loop: think, act, observe, repeat — turning chaos into ordered steps.*
## The Problem

启动 REPL，给 Agent 一个复杂任务：

```
You: 帮我创建一个叫 mylib 的 Python 包，要求：
     1) 有 setup.py
     2) 有 README.md 说明用法
     3) 有一个 mylib/__init__.py 导出版本号
     4) 有 tests/test_basic.py 基本测试
     5) 运行测试确认通过
```

没有规划能力的 Agent 可能会这样：创建 setup.py → 忘了 README → 直接跑测试 → 测试失败因为没有 `__init__.py` → 回头补 → 再跑测试 → 忘记 README 还没写......

它不是不能做，而是不知道自己"做到哪了"。人类在处理复杂任务时会列一个清单打勾，Agent 也需要一个。

## The Solution

引入一个新模块 `todo.py`，包含一个 `TodoManager` 类和一个 `todo` 工具。

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

## TodoManager 设计

`TodoManager` 是一个内存中的任务列表管理器。创建 `todo.py`：

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

数据结构很简单：一个字典列表，每项有 `id`、`content`、`status`。

关键设计决策：

**同一时间只能有一个 `in_progress`**。为什么？因为 Agent 是单线程的——它一次只能做一件事。如果允许多个 `in_progress`，Agent 会在任务间跳来跳去，反而降低效率。这个约束强制 Agent 线性地完成任务。

**返回字符串而非抛异常**。和 Chapter 2 的工具设计原则一致——错误信息是给 LLM 看的，它能理解并修正。

## 实现 todo 工具

todo 工具是一个"多操作"工具——一个工具支持 `add`、`update_status`、`list` 三种操作：

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

> **Note**: 为什么不把 add、update、list 拆成三个独立工具？因为它们在概念上是一个功能——任务管理。LLM 更容易理解"一个叫 todo 的工具"而不是"todo_add、todo_update、todo_list 三个工具"。一般来说，同一领域的紧密相关操作适合合并，不相关的操作应该分开。

handler 函数通过 `make_todo_handler` 工厂函数创建，绑定到特定的 TodoManager 实例：

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

## 提醒机制

有了 todo 工具，LLM 不一定会主动使用它。它可能拆解了任务，然后埋头执行，忘记更新状态。

解决方案是"nag reminder"——如果 Agent 连续 3 轮没有调用 todo 工具，自动注入一条提醒消息：

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

在 `agent_loop` 中，每轮开始时调用 `tick()`：

```python
# agent_loop 中 — NEW
if todo_manager is not None:
    reminder = todo_manager.tick()
    if reminder:
        messages.append({"role": "user", "content": reminder})
```

这是一个"引导而非强制"的设计。提醒以 `<reminder>` 标签包裹，LLM 能理解这是系统提示而非用户输入。如果确实不需要更新 todo，LLM 可以忽略它。

## 集成到 Agent

在 `agent.py` 中的改动很小：

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

核心循环的结构依然不变。我们只是添加了一个工具和一个提醒注入点。

## 规划 vs 执行

有了 todo 工具后，Agent 有两种工作模式：

**Plan-then-Execute**：先把所有步骤列出来，然后逐个执行。适合目标明确的任务。

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

**Interleaved**（交错模式）：边规划边执行，根据执行结果动态调整计划。适合探索性任务。

两种模式各有优势。系统提示词中的"收到复杂任务时，先用 todo 工具拆解为步骤"引导 Agent 倾向 Plan-then-Execute，但不强制。

> **Tip**: 如果你想让 Agent 更严格地遵循 Plan-then-Execute，可以在系统提示词中加入"在标记第一个任务为 in_progress 之前，确保已列出所有步骤"。但过于严格的规则会降低灵活性——有些任务在执行前无法完全规划。

## 运行效果

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

注意 Agent 的行为：先规划 5 个步骤，然后按顺序逐个执行，每步开始标记 `in_progress`，完成标记 `completed`。有序、可追踪。

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 无任务管理，复杂任务靠"记忆"维持 | TodoManager 追踪每个步骤 |
| Agent 可能跳步、重复、忘记目标 | 明确的 pending → in_progress → completed 流转 |
| 4 个工具 | 5 个工具 (+todo) |
| 1 个文件 (agent.py) | 2 个文件 (agent.py + todo.py) |

**Cumulative capability**: 你的 MiniAgent 现在能执行命令、读写文件、多轮对话、规划多步骤任务并追踪进度。

## Try It Yourself

1. **Verify**: 给 Agent 一个 5 步以上的任务，观察它是否先规划再执行。在执行过程中让它 `todo list`，确认状态正确。

2. **Extend**: 给 TodoManager 添加一个 `remove` 操作，允许 Agent 删除不再需要的任务。更新 `handle_todo` 和 `TODO_TOOL` schema。

3. **Explore**: 在 REPL 中连续 5 轮不使用 todo 工具，观察提醒机制是否触发。思考：如果 Agent 忽略了提醒怎么办？有没有更强的约束手段？（提示：可以将 todo 列表注入 system prompt，但这有 token 成本。）

## Summary

- **TodoManager** 提供 add / update_status / list 三个操作来管理任务列表
- **单 in_progress 约束**强制 Agent 线性执行，避免在任务间跳跃
- **提醒机制**（nag reminder）在 Agent 连续 3 轮不更新 todo 时注入提示
- **工厂函数模式** `make_todo_handler(manager)` 将工具 handler 绑定到特定状态实例
- Plan-then-Execute 适合目标明确的任务，Interleaved 适合探索性任务
- 本章引入了第一个**独立模块** `todo.py`——后续每个新能力都会是一个新模块

下一章，你将让 Agent 能够按需加载领域知识，而不是把所有知识塞进系统提示词。

## Further Reading

- Yao, S., et al. (2023). "ReAct: Synergizing Reasoning and Acting in Language Models." *ICLR 2023* — 推理-行动交错模式的理论基础
- Wei, J., et al. (2022). "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." *NeurIPS 2022* — 让 LLM 分步思考的经典方法
