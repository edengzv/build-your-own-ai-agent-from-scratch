<!-- Translated from: ch11-team-protocols.md -->

# Chapter 11: Team Protocols

> **Motto**: "Teammates need shared rules of communication."

> In Chapter 10, your teammates can communicate — Lead sends messages, teammates reply. But this free-text communication lacks structure. Consider this scenario: you want to shut down a reviewer teammate that is still working. You send `send("reviewer", "Please stop working and exit")`. The problem is: the reviewer is in the middle of editing a file. It receives the "stop" message and exits immediately, leaving a half-written file behind. This chapter introduces request-response protocols — structured communication flows for specific operations that ensure critical actions happen safely and in order.

![Conceptual: Structured protocol messages](images/ch11/fig-11-01-concept.png)

*Figure 11-1. Team protocols: structured, reliable communication between collaborating agents.*
## The Problem

The mailbox system from the previous chapter is "primitive" — you can send anything, but that also means there are no guarantees:

```
You: Shut down the reviewer

Agent: [Tool: send] → reviewer：请停止你当前的工作并退出

  // reviewer 正在 agent.py 的第 200 行做编辑...
  // 收到消息后直接退出了
  // 文件处于半完成状态

Agent: 已通知审查员停止
```

Similarly, if the reviewer wants to propose a refactoring plan, the only option is to send it to Lead as free text. Lead sees the message and verbally says "agreed," but there is no record. Was the plan formally approved? What conditions were attached to the approval? This information is lost as the conversation context gets compressed.

What we need is not more messages — it is **structured communication flows**.

## 11.1 The Request-Response Pattern

The solution is to introduce **protocols** — a request-response pattern backed by a state machine:

```
发起方 → 创建请求（pending）→ 通知对方
对方   → 看到请求 → 处理 → 响应（approved / rejected）
发起方 → 查看响应 → 根据结果行动
```

Each request is a JSON file, stored in the `.team/protocols/` directory:

```
.team/
├── inbox/         ← 自由消息（第 10 章）
└── protocols/     ← 结构化协议请求
    ├── shutdown_a1b2c3d4.json
    └── plan_e5f6g7h8.json
```

The request **state machine** is dead simple:

```
pending → approved → completed
       └→ rejected
```

`pending` is the initial state. Once the other party responds, it becomes `approved` or `rejected`. This guarantees three things:
1. Every request has a definitive outcome — nothing falls into a black hole
2. Outcomes are persisted in files — immune to context compression
3. You can query a request's current status at any time

## 11.2 The Shutdown Protocol

The first protocol: safely shutting down a teammate.

**Flow**:

```
Lead: shutdown_request("reviewer", reason="任务完成")
  → 创建 shutdown_a1b2c3d4.json (status: pending)
  → 通知 reviewer 有关闭请求

Reviewer: (处理完当前工作后)
  shutdown_respond("shutdown_a1b2c3d4", approve=True, note="当前审查已完成")
  → 更新状态为 approved
  → 安全退出循环

Lead: protocol_list(type="shutdown")
  → 看到 [approved] shutdown_a1b2c3d4: 关闭 reviewer
```

The implementation is concise:

```python
def create_shutdown_request(target_name: str, reason: str = "") -> str:
    request_id = f"shutdown_{uuid.uuid4().hex[:8]}"
    req = {
        "id": request_id,
        "type": "shutdown",
        "target": target_name,
        "reason": reason,
        "status": "pending",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "responded_at": "",
        "response_note": "",
    }
    _save_request(req)
    return f"关闭请求 {request_id} 已创建，等待 {target_name} 响应"
```

The teammate's response function:

```python
def respond_shutdown(request_id, approve, note=""):
    req = _load_request(request_id)
    # 验证：存在、类型正确、状态为 pending
    req["status"] = "approved" if approve else "rejected"
    req["responded_at"] = time.strftime(...)
    req["response_note"] = note
    _save_request(req)
```

Notice the three layers of validation: the request must exist, must be of type `shutdown`, and must be in the `pending` state. This prevents duplicate responses and type confusion.

## 11.3 The Plan Approval Protocol

The second protocol: a teammate submits a plan, Lead approves it.

**Flow**:

```
Reviewer: plan_request(
    summary="重构 agent_loop 为异步模式",
    details="1. 将 while True 改为 asyncio\n2. 工具调用并行化\n3. ..."
)
  → 创建 plan_e5f6g7h8.json (status: pending)

Lead: 收到通知 → 查看方案详情
  plan_review("plan_e5f6g7h8", approve=True, note="同意，但先做单元测试")
  → 更新状态为 approved

Reviewer: 查看结果 → 开始执行方案
```

```python
def create_plan_request(author, plan_summary, plan_details=""):
    request_id = f"plan_{uuid.uuid4().hex[:8]}"
    req = {
        "id": request_id,
        "type": "plan",
        "author": author,
        "summary": plan_summary,
        "details": plan_details,
        "status": "pending",
        ...
    }
    _save_request(req)
```

The approval function is structurally almost identical to the shutdown response — the state machine is universal, only the request type differs.

## 11.4 Tool Grouping: Lead vs Teammate

Protocol tools are grouped by role:

| Role | Tool | Function |
|------|------|----------|
| **Lead** | `shutdown_request` | Initiate a shutdown request |
| **Lead** | `plan_review` | Approve or reject a plan |
| **Lead** | `protocol_list` | View all requests |
| **Teammate** | `shutdown_respond` | Respond to a shutdown request |
| **Teammate** | `plan_request` | Submit a plan |

```python
LEAD_PROTOCOL_TOOLS = [SHUTDOWN_REQ_TOOL, PLAN_REVIEW_TOOL, PROTOCOL_LIST_TOOL]
TEAMMATE_PROTOCOL_TOOLS = [SHUTDOWN_RESP_TOOL, PLAN_REQ_TOOL]
```

This is an important design choice: different roles get different subsets of tools. Lead can initiate and approve; Teammate can respond and submit. Nobody can both initiate and respond to their own request.

**Factory functions** create the handlers:

```python
def make_lead_protocol_handlers():
    return {
        "shutdown_request": lambda target, reason="": create_shutdown_request(target, reason),
        "plan_review": lambda request_id, approve, note="": review_plan(request_id, approve, note),
        "protocol_list": lambda status="", type="": list_requests(status, type),
    }

def make_teammate_protocol_handlers(teammate_name):
    return {
        "shutdown_respond": lambda request_id, approve, note="": respond_shutdown(request_id, approve, note),
        "plan_request": lambda summary, details="": create_plan_request(teammate_name, summary, details),
    }
```

`make_teammate_protocol_handlers` takes `teammate_name` as an argument — this way `plan_request` automatically knows who the author is, and the teammate never needs to declare its own name.

## 11.5 Integrating into the Agent

Changes in `agent.py`:

**Import the protocol module**:
```python
from protocols import (
    LEAD_PROTOCOL_TOOLS, TEAMMATE_PROTOCOL_TOOLS,
    make_lead_protocol_handlers, make_teammate_protocol_handlers,
)
```

**Extend the tool list**:
```python
TOOLS = [
    # ... 基础工具 ...
    *TEAM_TOOLS,
    *LEAD_PROTOCOL_TOOLS,  # NEW
]
```

**Extend `_PARENT_ONLY`**:
```python
_PARENT_ONLY = {
    "task", "bg_run", "bg_check",
    "task_create", "task_update", "task_list", "task_get",
    "spawn", "send", "inbox", "team_status",
    "shutdown_request", "plan_review", "protocol_list",  # NEW
}
```

**Inject protocol tools when spawning a teammate**:
```python
def handle_spawn(name, role):
    teammate_handlers = dict(child_handlers)
    teammate_handlers.update(make_teammate_protocol_handlers(name))  # NEW
    return team_manager.spawn(
        ...,
        tools=CHILD_TOOLS + TEAMMATE_PROTOCOL_TOOLS,  # CHANGED
        tool_handlers=teammate_handlers,
    )
```

**Register Lead protocol handlers**:
```python
handlers.update(make_lead_protocol_handlers())
```

## 11.6 Try It Out

```bash
cd miniagent
python agent.py
```

Try the plan approval flow:

```
You: 创建一个 reviewer 队友，让它提出一个代码改进方案

  [Tool: spawn] reviewer (代码审查员)
  [Tool: send] → reviewer：审查代码并提出一个改进方案，用 plan_request 提交

You: 查看待审批的方案

  [Tool: protocol_list] (protocol_list)

You: 批准方案，告诉它可以执行

  [Tool: plan_review] plan_xxx 批准
```

Try safe shutdown:

```
You: 关闭 reviewer 队友

  [Tool: shutdown_request] 关闭 reviewer
```

> **Try It Yourself**: Look inside the `.team/protocols/` directory at the JSON files. Try creating a plan request, then rejecting it (`approve=False`), and observe the state change.

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +15 行（协议导入、工具注册、队友协议注入）
├── protocols.py        ← NEW: 249 行（请求-响应协议、两组工具、工厂函数）
├── team.py
├── tasks.py
├── background.py
├── context.py
├── subagent.py
├── skill_loader.py
└── todo.py
```

| Metric | Chapter 10 | Chapter 11 |
|--------|-----------|------------|
| Tools | 18 | **23** (+shutdown_request, +plan_review, +protocol_list, +shutdown_respond, +plan_request) |
| Modules | 8 | **9** (+protocols.py) |
| Capability | Free-text communication | **+Structured protocols** |
| Communication | Mailbox messages | **+Request-response protocols** |

## Summary

- Free-text mailbox communication lacks guarantees — shutdown operations and plan approvals need structured flows
- A protocol is a request-response pattern with a state machine: pending -> approved / rejected
- Each request is an independent JSON file, immune to context compression
- The shutdown protocol ensures a teammate finishes its current work before safely exiting
- The plan approval protocol makes sure important teammate decisions go through Lead for confirmation
- Tools are grouped by role: Lead uses LEAD_PROTOCOL_TOOLS, Teammate uses TEAMMATE_PROTOCOL_TOOLS
- The factory function `make_teammate_protocol_handlers(name)` binds teammate identity via closure
