<!-- Translated from: ch10-agent-team.md -->

# Chapter 10: Agent Teams

> **Motto**: "When the task is too big for one, bring in teammates."

> Take a moment to review your agent's ability to divide labor. The sub-agents from Chapter 7 are one-shot — you call the `task` tool, it spins up a temporary agent that does its work and then vanishes. No name, no role, no memory across tasks. What if you need a "code reviewer" that repeatedly checks code quality? Initializing a fresh sub-agent from scratch every time is inefficient and lacks continuity. This chapter introduces persistent teammates: long-running instances with names, roles, their own independent agent loops, and communication through a mailbox system.

> **Part IV starting point**: This is the first chapter of the COLLABORATION phase. The next four chapters will build out a complete multi-agent collaboration system.

![Conceptual: Multi-agent team network](images/ch10/fig-10-01-concept.png)

*Figure 10-1. Agent team: specialized teammates connected by communication channels.*
## The Problem

Try this scenario: you are developing a complex project and need someone dedicated to code review.

```
You: 审查一下 agent.py 的代码质量

Agent: [Tool: task] 审查 agent.py
  (子智能体启动，读文件，给出审查意见，消失)

Agent: 审查结果如下...

You: 我根据你的建议改了代码，再审查一次

Agent: [Tool: task] 审查 agent.py
  (又一个全新的子智能体，不知道之前审查过什么)

Agent: 审查结果如下...
```

Every review starts from zero. The sub-agent does not remember what issues it found last time or what changes you made. It is a disposable helper, not a team member.

A more realistic scenario: you want a "test engineer" continuously running tests in the background and a "reviewer" checking every change. That requires multiple agents existing simultaneously, each with its own specialty, communicating with each other — the sub-agent pattern cannot do this.

## The Solution

Introduce **persistent teammates** — each teammate is a long-running agent instance:

```
Lead Agent (你对话的主 Agent)
  ├── spawn("reviewer", role="代码审查员")  → 启动队友
  ├── spawn("tester", role="测试工程师")    → 启动队友
  │
  ├── send("reviewer", "审查 agent.py")    → 发送任务
  ├── send("tester", "运行测试")           → 发送任务
  │
  └── inbox()                              → 查看回复
       "reviewer: 发现 3 个问题..."
       "tester: 全部通过"
```

Key characteristics:

1. **Persistent identity**: Each teammate has a name and role that persist across interactions
2. **Independent threads**: Each teammate runs its own agent loop in its own thread
3. **Mailbox communication**: File-based message passing (`.team/inbox/{name}.jsonl`)
4. **Lifecycle management**: spawn → IDLE ↔ WORKING → SHUTDOWN

## 10.1 The Teammate Data Structure

```python
@dataclass
class Teammate:
    """一个持久化队友的状态。"""
    name: str
    role: str
    status: str = "idle"  # idle | working | shutdown
    thread: threading.Thread | None = None
    created_at: float = field(default_factory=time.time)
```

Simple and clear. `status` has three states:

- **idle**: Waiting for tasks (polling the mailbox)
- **working**: Processing a message
- **shutdown**: Shut down

`thread` holds the teammate's running thread — each teammate is a daemon thread that terminates automatically when the main process exits.

## 10.2 TeamManager

```python
class TeamManager:
    def __init__(self):
        self._teammates: dict[str, Teammate] = {}
        self._lock = threading.Lock()
        os.makedirs(INBOX_DIR, exist_ok=True)
```

`_lock` protects concurrent access to the `_teammates` dictionary — multiple teammates may read and write simultaneously.

The **spawn method** creates and starts a teammate:

```python
def spawn(self, name, role, agent_loop_fn, tools, tool_handlers, system):
    # 检查是否已存在
    with self._lock:
        if name in self._teammates:
            existing = self._teammates[name]
            if existing.status != "shutdown":
                return f"[error: 队友 '{name}' 已存在且正在运行]"

    # 创建邮箱文件
    inbox_path = os.path.join(INBOX_DIR, f"{name}.jsonl")
    if not os.path.exists(inbox_path):
        open(inbox_path, "w").close()

    teammate = Teammate(name=name, role=role, status="idle")
    # ... 启动线程 ...
```

Notice two design decisions:

1. Names are unique — you cannot create two teammates with the same name
2. A teammate that has been shut down can be re-created with the same name

## 10.3 The Teammate Main Loop

Each teammate runs a loop in its own thread: check mailbox → process message → return to idle → repeat.

```python
def teammate_loop():
    client = anthropic.Anthropic()
    messages = []
    role_system = f"{system}\n\n你的角色: {role}\n你的名字: {name}"

    while teammate.status != "shutdown":
        # 检查邮箱
        inbox_messages = self._read_inbox_raw(name)
        if not inbox_messages:
            time.sleep(3)  # 空闲时轮询
            continue

        teammate.status = "working"
        for msg in inbox_messages:
            messages.append({"role": "user", "content": msg["content"]})

            # 运行 agent loop
            for _ in range(15):  # max turns per message
                response = client.messages.create(...)
                # ... 工具执行 ...
                if response.stop_reason != "tool_use":
                    # 将回复发送回 sender
                    self.send(sender, f"[来自 {name}] {reply}", from_name=name)
                    break

        teammate.status = "idle"
```

A few key points:

- **role_system**: The role and name are injected into the system prompt so the teammate knows who it is
- **messages persist**: The teammate's message list accumulates across tasks — it remembers what it has done before
- **15-turn cap**: Prevents infinite loops, a safety mechanism similar to what sub-agents use
- **Auto-reply**: After processing a message, the result is sent back to the sender's mailbox

This is the essential difference between teammates and sub-agents: a sub-agent is a fire-and-forget function call; a teammate is a background process that stays on the job.

## 10.4 The Mailbox Communication System

Communication is file-based — each agent has its own mailbox file:

```
.team/
└── inbox/
    ├── lead.jsonl      ← Lead Agent 的邮箱
    ├── reviewer.jsonl  ← 审查员的邮箱
    └── tester.jsonl    ← 测试员的邮箱
```

**JSONL format** (JSON Lines): one message per line, append-only:

```json
{"from": "lead", "to": "reviewer", "content": "审查 agent.py", "timestamp": "2025-01-15 10:30:00"}
{"from": "lead", "to": "reviewer", "content": "重点看错误处理", "timestamp": "2025-01-15 10:31:00"}
```

**Sending a message** — append to the recipient's mailbox file:

```python
def send(self, to_name, content, from_name="lead"):
    inbox_path = os.path.join(INBOX_DIR, f"{to_name}.jsonl")
    msg = {
        "from": from_name, "to": to_name,
        "content": content,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(inbox_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")
```

**Reading the mailbox** — read and clear (atomic operation):

```python
def _read_inbox_raw(self, name):
    with self._lock:
        with open(inbox_path, "r") as f:
            lines = f.readlines()
        if not lines:
            return []
        # 清空邮箱
        with open(inbox_path, "w") as f:
            pass
    return [json.loads(line) for line in lines if line.strip()]
```

Why "read and clear"? To prevent the same message from being processed twice. This is the simplest implementation of "exactly-once" semantics.

## 10.5 Four Tools

| Tool | Function | Use Case |
|---|---|---|
| `spawn` | Create a persistent teammate | When you need a specialized role |
| `send` | Send a message to a teammate | Assign tasks, provide feedback |
| `inbox` | Check the Lead's mailbox | Receive teammate replies |
| `team_status` | View all teammate statuses | Monitor the team |

## 10.6 Integrating into the Agent

`agent_loop` gains a `team_manager` parameter:

```python
def agent_loop(
    messages, todo_manager=None, context_manager=None,
    bg_manager=None, task_graph=None,
    team_manager=None,  # NEW
):
```

There is a special detail in how the team tool handlers are registered — `handle_spawn` needs to pass the agent's tool set and system prompt to the new teammate:

```python
if team_manager is not None:
    def handle_spawn(name, role):
        return team_manager.spawn(
            name=name, role=role,
            agent_loop_fn=agent_loop,
            tools=CHILD_TOOLS,         # 队友用子工具集
            tool_handlers=child_handlers,
            system=SYSTEM_TEMPLATE,
        )
    handlers["spawn"] = handle_spawn
    handlers["send"] = lambda to, content: team_manager.send(to, content)
    handlers["inbox"] = lambda: team_manager.read_inbox("lead")
    handlers["team_status"] = lambda: team_manager.list_teammates()
```

Teammates use `CHILD_TOOLS` — just like sub-agents, they cannot spawn new teammates or use other Lead-exclusive tools.

**Mailbox messages are auto-injected**: Before each LLM call, the Lead's mailbox is checked and injected:

```python
if team_manager is not None:
    inbox_msg = team_manager.read_inbox("lead")
    if not inbox_msg.endswith("为空"):
        messages.append({"role": "user", "content": f"<team-inbox>\n{inbox_msg}\n</team-inbox>"})
```

This follows the same pattern as background task notifications — passive injection that lets the Lead agent naturally handle teammate replies.

## 10.7 Lead vs Teammate

| | Lead Agent | Teammate |
|---|---|---|
| **How it starts** | Direct user conversation | Created by Lead via spawn |
| **Lifecycle** | Follows the REPL session | spawn → shutdown |
| **Tool set** | Full TOOLS (18 tools) | CHILD_TOOLS (basic tools) |
| **Unique capabilities** | spawn/send/inbox/team_status | Auto-reply to sender |
| **Message source** | User input | Mailbox messages |

The Lead is the "manager," responsible for planning and coordination. Teammates are the "executors," responsible for completing specific tasks.

## 10.8 Try It Out

```bash
cd miniagent
python agent.py
```

```
工具: bash, read_file, write_file, edit_file, todo, load_skill, compact, task,
      bg_run, bg_check, task_create, task_update, task_list, task_get,
      spawn, send, inbox, team_status
```

Try creating a reviewer:

```
You: 创建一个代码审查员队友，然后让它审查 agent.py
```

Watch how the agent:
1. Uses `spawn` to create a "reviewer" teammate
2. Uses `send` to dispatch the review task
3. After a moment, uses `inbox` to check the review results

```
You: 查看团队状态
```

```
You: 让审查员再看一下 team.py
```

Notice that this time, the reviewer remembers the previous review — its message list has maintained context across tasks.

> **Try It Yourself**: Look at the JSONL files in the `.team/inbox/` directory. Try manually writing a message to the reviewer's mailbox and see if the teammate picks it up and processes it.

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +30 lines (team_manager param, handler registration, mailbox injection)
├── todo.py
├── skill_loader.py
├── context.py
├── subagent.py
├── background.py
├── tasks.py
├── team.py             ← NEW: 259 lines (TeamManager, mailbox communication, 4 tools)
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| Metric | Chapter 9 | Chapter 10 |
|------|-----------|------------|
| Tool count | 14 | **18** (+spawn, +send, +inbox, +team_status) |
| Module count | 7 | **8** (+team.py) |
| Capabilities | Persistent task DAG | **+Persistent teammate teams** |
| Division of labor | One-shot sub-agents | **+Long-running teammates** |

**Sub-agents vs teammates** — when to use which?

- **Sub-agent (task)**: One-shot tasks that do not need memory across tasks. "Help me search for the answer to this question."
- **Teammate (spawn)**: Long-term roles that need cross-task continuity. "I need a reviewer that stays online."

The next chapter will add structured communication protocols to the team — graceful shutdown, proposal approval, and other request-response patterns.

## Summary

- Sub-agents are one-shot function calls; teammates are persistent background processes
- TeamManager manages teammate lifecycles: spawn → IDLE ↔ WORKING → SHUTDOWN
- The mailbox system is file-based (`.team/inbox/{name}.jsonl`), uses JSONL format, and clears on read
- Teammates run their own agent loops in independent threads, with messages accumulating across tasks
- The Lead agent manages the team through four tools: spawn/send/inbox/team_status
- Teammates use CHILD_TOOLS and cannot create new teammates or use Lead-exclusive tools
- Mailbox messages are auto-injected before each LLM call, following the same pattern as background notifications
