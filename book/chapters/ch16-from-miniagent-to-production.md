# Chapter 16: 从 MiniAgent 到生产

> **Motto**: "你已经理解了原理，现在看看真实世界"

> 这是本书的最后一章。不写新代码——而是带你回顾 16 章构建的完整系统，用 MiniAgent 的概念映射真实世界的 Agent 框架，并讨论走向生产的策略。你已经从 30 行代码成长为一个拥有 13 个模块、29 个工具的多智能体系统。这一章是你"毕业"的时刻。

## 16.1 MiniAgent 全景回顾

让我们从高处俯瞰你构建的完整系统：

```
miniagent/
├── agent.py          ← 主入口：548 行，Agent 循环 + REPL
├── todo.py           ← 任务规划：TodoManager + 提醒注入
├── skill_loader.py   ← 知识加载：两层 Skill 注入
├── context.py        ← 上下文管理：三层压缩策略
├── subagent.py       ← 子智能体：独立上下文的任务委托
├── background.py     ← 后台任务：daemon 线程 + 通知队列
├── tasks.py          ← 持久化任务：文件级 DAG 任务图
├── team.py           ← 团队：持久化队友 + 邮箱通信
├── protocols.py      ← 协议：请求-响应 + 状态机
├── autonomous.py     ← 自主：IDLE/WORK 循环 + 任务认领
├── worktree.py       ← 隔离：Git Worktree 绑定任务
├── security.py       ← 安全：沙箱 + 命令分级 + RBAC
└── observability.py  ← 可观测：日志 + 追踪 + Token 统计
```

### 五个阶段的成长路径

| 阶段 | 章节 | 核心能力 | 代码增长 |
|------|------|---------|---------|
| **THE LOOP** | Ch1-3 | 基础循环、工具调用、对话记忆 | 30 → 200 行 |
| **THE HARNESS** | Ch4-6 | 任务规划、知识加载、上下文管理 | 200 → 600 行 |
| **SCALE** | Ch7-9 | 子智能体、后台任务、持久化任务图 | 600 → 1200 行 |
| **COLLABORATION** | Ch10-13 | 团队、协议、自主、工作隔离 | 1200 → 2400 行 |
| **PRODUCTION** | Ch14-16 | 安全、可观测性、生产策略 | 2400 → 2950 行 |

### 核心设计模式

回顾贯穿全书的设计模式：

1. **Agent = Model + Harness**：LLM 负责决策，Harness 负责执行。这个公式在第 1 章提出，16 章后依然成立。

2. **工具注册表模式**：`handlers = {name: function}`。从第 2 章的 3 个工具到第 15 章的 29 个工具，注册方式从未改变。

3. **工厂函数闭包**：`make_xxx_handler(state)` 返回绑定了状态的函数。从 `make_todo_handler` 到 `make_security_wrapper`，解决了全局状态问题。

4. **被动注入模式**：在 LLM 调用前注入提醒/通知/邮箱消息。不需要 Agent 主动检查，系统自动推送。

5. **文件即数据库**：`.tasks/*.json`、`.team/inbox/*.jsonl`、`.team/protocols/*.json`、`.logs/*.jsonl`。简单可靠，人类可读。

## 16.2 映射真实框架

用 MiniAgent 的概念理解真实世界的 Agent 框架：

### LangChain

| MiniAgent 概念 | LangChain 对应 |
|---------------|---------------|
| TOOLS 列表 | `@tool` 装饰器 + ToolKit |
| agent_loop | AgentExecutor |
| handlers 映射 | Tool.run() |
| SYSTEM_TEMPLATE | SystemMessage |
| context.py 压缩 | ConversationSummaryMemory |

LangChain 的 "Chain" 就是我们的 agent_loop 的抽象化。

### AutoGen

| MiniAgent 概念 | AutoGen 对应 |
|---------------|-------------|
| TeamManager | GroupChat |
| Teammate | ConversableAgent |
| 邮箱通信 | message passing |
| spawn/send | register_agent / send |
| protocols.py | termination conditions |

AutoGen 的多 Agent 对话模式和我们的 Team 系统非常相似——本质都是独立 Agent 实例通过消息通信。

### CrewAI

| MiniAgent 概念 | CrewAI 对应 |
|---------------|------------|
| spawn(name, role) | Agent(role, goal, backstory) |
| task_create | Task(description, agent) |
| TEAMMATE_TOOLS | agent.tools |
| autonomous.py | Process.sequential / hierarchical |

CrewAI 的 "Crew" 就是我们 TeamManager 的高级封装。

### Claude Code (Anthropic)

| MiniAgent 概念 | Claude Code 对应 |
|---------------|----------------|
| agent_loop | Session main loop |
| TOOLS | Tool definitions |
| handlers | Tool handlers |
| context.py | Context window management |
| subagent.py | Task tool (subagent) |
| security.py | Permission system |
| observability.py | Token tracking |

Claude Code 是最接近 MiniAgent 的真实产品——事实上，MiniAgent 的很多设计灵感来自对 Claude Code 架构的研究。

## 16.3 部署架构模式

将 MiniAgent 部署到生产环境的三种模式：

### CLI Agent（当前模式）

```
用户 ←→ 终端 REPL ←→ agent_loop ←→ LLM API
```

适用：开发者工具、本地助手。就是你一直在用的模式。

### API Agent

```
HTTP 请求 → Web 框架 → agent_loop → 返回结果
```

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/agent", methods=["POST"])
def run_agent():
    user_input = request.json["message"]
    messages = [{"role": "user", "content": user_input}]
    agent_loop(messages, ...)
    return jsonify({"response": messages[-1]["content"]})
```

适用：SaaS 产品、聊天机器人后端。需要添加认证、限流、异步处理。

### Event-Driven Agent

```
事件源 (GitHub webhook, Slack) → 消息队列 → agent_loop → 回调
```

适用：自动化流程——PR 审查、Issue 处理、监控告警。Agent 被事件触发而不是用户输入。

## 16.4 成本控制

Token 是 Agent 最大的运营成本。优化策略：

1. **上下文压缩**：你在第 6 章已经实现了。生产中需要更激进的策略——只保留最相关的 N 轮对话。

2. **缓存**：相同的文件读取不需要每次都占用 context。实现 Tool 结果缓存。

3. **模型分级**：大模型（Claude Sonnet）做规划和决策，小模型（Haiku）做简单的工具调用和格式化。

4. **Token 预算**：设置每次交互的 Token 上限。超过预算时强制压缩或终止。

```python
# 伪代码：成本感知的 Agent 循环
MAX_COST_PER_SESSION = 1.0  # $1

while True:
    if obs.stats.estimated_cost() > MAX_COST_PER_SESSION:
        print("⚠️ 已达到成本上限")
        break
    response = client.messages.create(...)
```

## 16.5 Agent 的未来

### 从工具使用到环境交互

MiniAgent 通过工具操作世界——bash、文件读写。下一步是更丰富的环境交互：浏览器操作（点击、输入、截图）、API 调用、GUI 操作。

### 从单模态到多模态

当前 Agent 只处理文本。多模态 Agent 能看截图（"这个 UI 有什么问题？"）、听语音（"帮我转录这段会议"）、生成图片（"画一个架构图"）。

### 从辅助到自主

MiniAgent 的自主程度在第 12 章达到了一个平衡点——队友自动认领任务，但重要决策需要 Lead（人类的代理）审批。真正的自主 Agent 需要更强的自我评估、错误恢复和对齐机制。

### 保持务实

Agent 技术正在快速发展，但核心原理是稳定的：

- **Agent = Model + Harness** 不会变
- **工具调用** 是 Agent 的基础能力
- **上下文管理** 是永恒的挑战
- **安全** 只会越来越重要

你已经掌握了这些原理。无论框架如何变化，你都能理解它们在做什么。

## 16.6 总结与下一步

### 你在这本书中学到了什么

1. **Agent 不是魔法**——它是一个 while 循环加上工具调用
2. **Harness 是核心**——LLM 能力相同时，Harness 决定 Agent 的能力边界
3. **渐进式构建**——从 30 行到 3000 行，每一步都可运行、可理解
4. **设计模式可复用**——工具注册表、工厂闭包、被动注入、文件即数据库

### 推荐的进阶路径

1. **添加更多工具**：Web 搜索、数据库操作、邮件发送。你已经知道模式——定义 schema、写 handler、注册到 handlers。

2. **替换 LLM**：把 Anthropic 换成 OpenAI、本地模型（Ollama）。只需要适配 API 格式，Agent 循环不变。

3. **添加 Web UI**：用 Flask/FastAPI 把 REPL 变成 Web 界面。Agent 循环是现成的。

4. **研究真实框架**：带着 MiniAgent 的理解去读 LangChain、AutoGen、CrewAI 的源码。你会发现很多似曾相识的模式。

5. **部署到生产**：选择一个真实场景——代码审查、文档生成、数据分析——把 MiniAgent 部署上去。

### 最后一句话

> Agent 的核心从未改变：一个 while 循环，一组工具，和一个 LLM。你现在理解了这一点。去构建属于你自己的 Agent 吧。

## Summary

- 16 章构建了 13 个模块、29 个工具、约 3000 行代码的多智能体系统
- 五个阶段：THE LOOP → THE HARNESS → SCALE → COLLABORATION → PRODUCTION
- 核心设计模式：Agent = Model + Harness、工具注册表、工厂闭包、被动注入、文件即数据库
- MiniAgent 的概念可以直接映射到 LangChain、AutoGen、CrewAI、Claude Code
- 生产部署有三种模式：CLI Agent、API Agent、Event-Driven Agent
- 成本控制通过上下文压缩、缓存、模型分级和 Token 预算实现
- Agent 技术的核心原理是稳定的：Model + Harness + Tools + Context
