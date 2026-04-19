# Chapter 11: 团队协议

> **Motto**: "队友需要共享的沟通规则"

> 第 10 章的队友能通信了——Lead 发消息，队友回复。但这种自由文本通信缺乏结构。考虑这个场景：你想关闭一个正在工作的审查员队友。你发送 `send("reviewer", "请停止工作并退出")`。问题是：审查员正在执行文件编辑的中间步骤。它收到"停止"消息后直接退出，留下一个写了一半的文件。本章引入请求-响应协议——为特定操作定义结构化的沟通流程，确保关键操作安全有序。

![Conceptual: Structured protocol messages](images/ch11/fig-11-01-concept.png)

*Figure 11-1. Team protocols: structured, reliable communication between collaborating agents.*
## The Problem

上一章的邮箱系统是"原始的"——发什么都行，但也意味着没有任何保障：

```
You: 关闭审查员

Agent: [Tool: send] → reviewer：请停止你当前的工作并退出

  // reviewer 正在 agent.py 的第 200 行做编辑...
  // 收到消息后直接退出了
  // 文件处于半完成状态

Agent: 已通知审查员停止
```

类似地，如果审查员想提出一个重构方案，它只能通过自由文本发送给 Lead。Lead 看到消息后口头说"同意"，但没有任何记录。方案是否被正式批准？批准附带什么条件？这些信息随着对话上下文的压缩而丢失。

我们需要的不是更多消息，而是**结构化的通信流程**。

## 11.1 请求-响应模式

解决方案是引入**协议**——一种带有状态机的请求-响应模式：

```
发起方 → 创建请求（pending）→ 通知对方
对方   → 看到请求 → 处理 → 响应（approved / rejected）
发起方 → 查看响应 → 根据结果行动
```

每个请求是一个 JSON 文件，存储在 `.team/protocols/` 目录：

```
.team/
├── inbox/         ← 自由消息（第 10 章）
└── protocols/     ← 结构化协议请求
    ├── shutdown_a1b2c3d4.json
    └── plan_e5f6g7h8.json
```

请求的**状态机**非常简单：

```
pending → approved → completed
       └→ rejected
```

`pending` 是初始状态。对方响应后变为 `approved` 或 `rejected`。这确保了：
1. 每个请求都有明确的结果——不会"石沉大海"
2. 结果持久化在文件中——不受上下文压缩影响
3. 任何时候都可以查询请求的当前状态

## 11.2 关闭协议

第一个协议：安全关闭队友。

**流程**：

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

实现很简洁：

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

队友的响应函数：

```python
def respond_shutdown(request_id, approve, note=""):
    req = _load_request(request_id)
    # 验证：存在、类型正确、状态为 pending
    req["status"] = "approved" if approve else "rejected"
    req["responded_at"] = time.strftime(...)
    req["response_note"] = note
    _save_request(req)
```

注意三层验证：请求必须存在、必须是 shutdown 类型、必须处于 pending 状态。这防止了重复响应或类型混乱。

## 11.3 方案审批协议

第二个协议：队友提交方案，Lead 审批。

**流程**：

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

审批函数结构和关闭响应几乎相同——状态机是通用的，只是请求类型不同。

## 11.4 工具分组：Lead vs Teammate

协议工具按角色分组：

| 角色 | 工具 | 功能 |
|------|------|------|
| **Lead** | `shutdown_request` | 发起关闭请求 |
| **Lead** | `plan_review` | 审批方案 |
| **Lead** | `protocol_list` | 查看所有请求 |
| **Teammate** | `shutdown_respond` | 响应关闭请求 |
| **Teammate** | `plan_request` | 提交方案 |

```python
LEAD_PROTOCOL_TOOLS = [SHUTDOWN_REQ_TOOL, PLAN_REVIEW_TOOL, PROTOCOL_LIST_TOOL]
TEAMMATE_PROTOCOL_TOOLS = [SHUTDOWN_RESP_TOOL, PLAN_REQ_TOOL]
```

这是一个重要的设计：不同角色使用不同的工具子集。Lead 能发起和审批，Teammate 能响应和提交。没有人能既发起又响应自己的请求。

**工厂函数**创建 handler：

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

`make_teammate_protocol_handlers` 接收 `teammate_name`——这样 `plan_request` 就自动知道作者是谁，队友不需要声明自己的名字。

## 11.5 集成到 Agent

在 `agent.py` 中的变更：

**导入协议模块**：
```python
from protocols import (
    LEAD_PROTOCOL_TOOLS, TEAMMATE_PROTOCOL_TOOLS,
    make_lead_protocol_handlers, make_teammate_protocol_handlers,
)
```

**扩展工具列表**：
```python
TOOLS = [
    # ... 基础工具 ...
    *TEAM_TOOLS,
    *LEAD_PROTOCOL_TOOLS,  # NEW
]
```

**扩展 _PARENT_ONLY**：
```python
_PARENT_ONLY = {
    "task", "bg_run", "bg_check",
    "task_create", "task_update", "task_list", "task_get",
    "spawn", "send", "inbox", "team_status",
    "shutdown_request", "plan_review", "protocol_list",  # NEW
}
```

**队友 spawn 时注入协议工具**：
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

**注册 Lead 协议 handler**：
```python
handlers.update(make_lead_protocol_handlers())
```

## 11.6 试一试

```bash
cd miniagent
python agent.py
```

试试方案审批流程：

```
You: 创建一个 reviewer 队友，让它提出一个代码改进方案

  [Tool: spawn] reviewer (代码审查员)
  [Tool: send] → reviewer：审查代码并提出一个改进方案，用 plan_request 提交

You: 查看待审批的方案

  [Tool: protocol_list] (protocol_list)

You: 批准方案，告诉它可以执行

  [Tool: plan_review] plan_xxx 批准
```

试试安全关闭：

```
You: 关闭 reviewer 队友

  [Tool: shutdown_request] 关闭 reviewer
```

> **Try It Yourself**：查看 `.team/protocols/` 目录中的 JSON 文件。试着创建一个方案请求，然后拒绝它（`approve=False`），观察状态变化。

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

| 指标 | Chapter 10 | Chapter 11 |
|------|-----------|------------|
| 工具数 | 18 | **23** (+shutdown_request, +plan_review, +protocol_list, +shutdown_respond, +plan_request) |
| 模块数 | 8 | **9** (+protocols.py) |
| 能力 | 自由文本通信 | **+结构化协议** |
| 通信方式 | 邮箱消息 | **+请求-响应协议** |

## Summary

- 自由文本邮箱通信缺乏保障——关闭操作和方案审批需要结构化流程
- 协议是带状态机的请求-响应模式：pending → approved / rejected
- 每个请求是独立的 JSON 文件，不受上下文压缩影响
- 关闭协议确保队友完成当前工作后再安全退出
- 方案审批协议让队友的重要决策经过 Lead 确认
- 工具按角色分组：Lead 用 LEAD_PROTOCOL_TOOLS，Teammate 用 TEAMMATE_PROTOCOL_TOOLS
- 工厂函数 `make_teammate_protocol_handlers(name)` 通过闭包绑定队友身份
