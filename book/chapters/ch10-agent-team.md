# Chapter 10: 智能体团队

> **Motto**: "当任务太大，一个人搞不定，就找队友"

> 回顾一下你的 Agent 的"分工"能力。第 7 章的子智能体是一次性的——你调用 `task` 工具，它创建一个临时 Agent 完成工作，然后就消失了。没有名字、没有角色、没有跨任务的记忆。如果你需要一个"代码审查员"反复检查代码质量呢？每次都从头初始化一个子智能体，效率低下且缺乏连续性。本章引入持久化队友：有名字、有角色、有自己独立的 Agent 循环、通过邮箱系统通信的长期运行实例。

> **Part IV 起点**：这是 COLLABORATION 阶段的第一章。接下来四章将构建完整的多智能体协作系统。

![Conceptual: Multi-agent team network](images/ch10/fig-10-01-concept.png)

*Figure 10-1. Agent team: specialized teammates connected by communication channels.*
## The Problem

试试这个场景：你在开发一个复杂项目，需要一个人专门负责代码审查。

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

每次审查都是从零开始。子智能体不记得上次发现了什么问题、你做了什么修改。它是一次性的帮手，不是团队成员。

更实际的场景：你想让一个"测试工程师"在后台持续运行测试，一个"审查员"检查每次修改。这需要多个 Agent 同时存在、各司其职、互相通信——子智能体模式做不到。

## The Solution

引入**持久化队友**——每个队友是一个长期运行的 Agent 实例：

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

关键特性：

1. **持久化身份**：每个队友有名字和角色，跨多次交互保持
2. **独立线程**：每个队友在自己的线程中运行独立的 Agent 循环
3. **邮箱通信**：基于文件的消息传递（`.team/inbox/{name}.jsonl`）
4. **生命周期管理**：spawn → IDLE ↔ WORKING → SHUTDOWN

## 10.1 Teammate 数据结构

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

简单明了。`status` 有三个状态：

- **idle**：等待任务（轮询邮箱）
- **working**：正在处理消息
- **shutdown**：已关闭

`thread` 保存队友的运行线程——每个队友是一个 daemon 线程，主进程退出时自动终止。

## 10.2 TeamManager

```python
class TeamManager:
    def __init__(self):
        self._teammates: dict[str, Teammate] = {}
        self._lock = threading.Lock()
        os.makedirs(INBOX_DIR, exist_ok=True)
```

`_lock` 保护 `_teammates` 字典的并发访问——多个队友可能同时读写。

**spawn 方法**创建并启动一个队友：

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

注意两个设计决策：

1. 名字唯一——不能创建两个同名队友
2. 已 shutdown 的队友可以用相同名字重新创建

## 10.3 队友的主循环

每个队友在自己的线程中运行一个循环：检查邮箱 → 处理消息 → 回到 idle → 重复。

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

几个要点：

- **role_system**：在系统提示词中注入角色和名字，让队友知道自己是谁
- **messages 保持**：队友的消息列表在多次任务间累积——它记得之前做过什么
- **15 轮上限**：防止无限循环，和子智能体类似的安全机制
- **自动回复**：处理完消息后，将结果发送回发送者的邮箱

这就是队友和子智能体的本质区别：子智能体是"用完即弃"的函数调用，队友是"驻留工作"的后台进程。

## 10.4 邮箱通信系统

通信基于文件——每个 Agent 有自己的邮箱文件：

```
.team/
└── inbox/
    ├── lead.jsonl      ← Lead Agent 的邮箱
    ├── reviewer.jsonl  ← 审查员的邮箱
    └── tester.jsonl    ← 测试员的邮箱
```

**JSONL 格式**（JSON Lines）：每行一条消息，append-only：

```json
{"from": "lead", "to": "reviewer", "content": "审查 agent.py", "timestamp": "2025-01-15 10:30:00"}
{"from": "lead", "to": "reviewer", "content": "重点看错误处理", "timestamp": "2025-01-15 10:31:00"}
```

**发送消息**——追加到目标的邮箱文件：

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

**读取邮箱**——读取并清空（原子操作）：

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

为什么要"读取并清空"？防止同一条消息被处理两次。这是最简单的"恰好一次"语义实现。

## 10.5 四个工具

| 工具 | 功能 | 场景 |
|---|---|---|
| `spawn` | 创建持久化队友 | 需要专业角色时 |
| `send` | 向队友发送消息 | 分配任务、提供反馈 |
| `inbox` | 查看 Lead 的邮箱 | 接收队友回复 |
| `team_status` | 查看所有队友状态 | 监控团队 |

## 10.6 集成到 Agent

`agent_loop` 增加 `team_manager` 参数：

```python
def agent_loop(
    messages, todo_manager=None, context_manager=None,
    bg_manager=None, task_graph=None,
    team_manager=None,  # NEW
):
```

团队工具的 handler 注册有个特别之处——`handle_spawn` 需要将 Agent 的工具集和系统提示传递给新队友：

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

队友使用 `CHILD_TOOLS`——和子智能体一样，不能 spawn 新队友或使用其他 Lead 专属工具。

**邮箱消息自动注入**：在每次 LLM 调用前，检查 Lead 的邮箱并注入：

```python
if team_manager is not None:
    inbox_msg = team_manager.read_inbox("lead")
    if not inbox_msg.endswith("为空"):
        messages.append({"role": "user", "content": f"<team-inbox>\n{inbox_msg}\n</team-inbox>"})
```

这和后台任务通知的模式一致——被动注入，让 Lead Agent 自然地处理队友的回复。

## 10.7 Lead vs Teammate

| | Lead Agent | Teammate |
|---|---|---|
| **启动方式** | 用户直接对话 | Lead 通过 spawn 创建 |
| **生命周期** | 跟随 REPL 会话 | spawn → shutdown |
| **工具集** | 完整 TOOLS（18 个） | CHILD_TOOLS（基础工具） |
| **特有能力** | spawn/send/inbox/team_status | 自动回复 sender |
| **消息来源** | 用户输入 | 邮箱消息 |

Lead 是"管理者"，负责规划和协调。Teammate 是"执行者"，负责完成具体任务。

## 10.8 试一试

```bash
cd miniagent
python agent.py
```

```
工具: bash, read_file, write_file, edit_file, todo, load_skill, compact, task,
      bg_run, bg_check, task_create, task_update, task_list, task_get,
      spawn, send, inbox, team_status
```

试试创建一个审查员：

```
You: 创建一个代码审查员队友，然后让它审查 agent.py
```

观察 Agent 如何：
1. 用 `spawn` 创建 "reviewer" 队友
2. 用 `send` 发送审查任务
3. 过一会儿用 `inbox` 查看审查结果

```
You: 查看团队状态
```

```
You: 让审查员再看一下 team.py
```

注意这次审查员记得之前的审查——它的消息列表保持了跨任务的上下文。

> **Try It Yourself**：查看 `.team/inbox/` 目录中的 JSONL 文件。试着手动写一条消息到 reviewer 的邮箱，看看队友会不会处理它。

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +30 行（team_manager 参数、handler 注册、邮箱注入）
├── todo.py
├── skill_loader.py
├── context.py
├── subagent.py
├── background.py
├── tasks.py
├── team.py             ← NEW: 259 行（TeamManager、邮箱通信、4 个工具）
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| 指标 | Chapter 9 | Chapter 10 |
|------|-----------|------------|
| 工具数 | 14 | **18** (+spawn, +send, +inbox, +team_status) |
| 模块数 | 7 | **8** (+team.py) |
| 能力 | 持久化任务 DAG | **+持久化队友团队** |
| 分工方式 | 一次性子智能体 | **+长期运行的队友** |

**子智能体 vs 队友**——何时用哪个？

- **子智能体 (task)**：一次性任务，不需要跨任务记忆。"帮我搜索这个问题的答案"
- **队友 (spawn)**：长期角色，需要跨任务连续性。"我需要一个一直在线的审查员"

下一章将为团队添加结构化的通信协议——安全关闭、方案审批等请求-响应模式。

## Summary

- 子智能体是一次性的函数调用，队友是持久化的后台进程
- TeamManager 管理队友的生命周期：spawn → IDLE ↔ WORKING → SHUTDOWN
- 邮箱系统基于文件（`.team/inbox/{name}.jsonl`），JSONL 格式，读取即清空
- 队友在独立线程中运行自己的 Agent 循环，消息跨任务累积
- Lead Agent 通过 spawn/send/inbox/team_status 四个工具管理团队
- 队友使用 CHILD_TOOLS，不能创建新队友或使用 Lead 专属工具
- 邮箱消息在每次 LLM 调用前自动注入，和后台通知模式一致
