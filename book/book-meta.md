# 智能体入门：从零构建通用 AI Agent
## Build Your Own AI Agent from Scratch

## Author
[Your Name]

## Target Audience

**Primary**: Python 开发者，有基本编程经验（函数、类、数据结构），对 AI Agent 感兴趣但没有实际构建经验的开发新手。

**Secondary**: 有一定 LLM 使用经验的产品经理和技术管理者，希望理解 Agent 内部工作原理。

**Readers should already know**:
- Python 基础（函数、类、字典、列表推导式）
- 命令行基本操作（cd, ls, pip install）
- 知道什么是 API 调用（不需要深入理解 HTTP）

**Readers do NOT need to know**:
- 机器学习或深度学习
- Transformer 架构或注意力机制
- 任何 Agent 框架（LangChain, AutoGen, CrewAI 等）
- 前端开发

## Book Synopsis

AI Agent 正在从实验室走向生产环境。然而，大多数教程要么停留在"调用 API + 写 Prompt"的浅层操作，要么直接跳到复杂框架的使用，读者知道怎么调用，却不知道 Agent 到底是如何工作的。

本书采用"从零构建"的方法论，带领读者从一个不到 30 行代码的 Agent 循环开始，逐章添加一个新能力——工具调用、任务规划、记忆管理、知识加载、上下文压缩、子智能体、多智能体协作——最终构建出一个功能完备的通用智能体系统。每一章的代码都是前一章的增量演进，读者在每一步都拥有一个可运行的完整系统。

读完本书，你将拥有一个自己从零编写的 Agent 系统，并深刻理解每一个组件为什么存在、如何工作、以及何时使用。这些知识让你能够评估任何 Agent 框架、定位生产环境中的问题、并根据实际需求设计自己的智能体架构。

## The Reader's Project

读者将从零构建一个名为 **MiniAgent** 的通用智能体系统。它是一个命令行程序，能够：
- 理解自然语言指令
- 自主选择和调用工具
- 规划多步骤任务
- 管理自身的记忆和上下文
- 加载领域知识
- 分派子任务给子智能体
- 与其他智能体协作完成复杂任务

最终代码量约 1,500-2,000 行 Python，不依赖任何 Agent 框架。

## Unique Value Proposition

| 差异点 | 本书 | 其他资源 |
|--------|------|----------|
| 方法论 | 从零构建，每章只加一个概念 | 框架教程，调 API |
| 代码 | 完整、可运行、无外部框架依赖 | 片段式、依赖特定框架 |
| 深度 | 理解 WHY，不只是 HOW | 大多只教 HOW |
| 进阶路径 | 从单 Agent 到多 Agent 协作 | 通常只覆盖单 Agent |
| 写作风格 | 循序渐进，每步可验证 | 知识灌输或快速入门 |

核心理念借鉴：
- **《深度学习入门：自制框架》**的"Step by Step 从零自制"哲学——每一章都在上一章的代码基础上增量演进
- **learn-claude-code** 的"Harness Engineering"思想——Agent = Model + Harness，我们构建的是 Harness

## Phase Map

### Phase 1: THE LOOP — 让 Agent 动起来 (Chapters 1-3)
**Milestone**: 一个能理解指令、调用工具、读写文件的基础 Agent

| # | Title | Motto | New Capability |
|---|-------|-------|----------------|
| 1 | 你好，Agent | "一个循环就是全部的开始" | 基础 Agent 循环 + bash 工具 |
| 2 | 工具调用 | "增加一个工具，只需增加一个处理函数" | 工具分发机制 (4 tools) |
| 3 | 对话记忆 | "没有记忆的 Agent 和函数调用没有区别" | 多轮对话 + 消息管理 |

### Phase 2: PLANNING — 让 Agent 会思考 (Chapters 4-6)
**Milestone**: 一个能规划任务、管理上下文、加载知识的智能 Agent

| # | Title | Motto | New Capability |
|---|-------|-------|----------------|
| 4 | 任务规划 | "没有计划的 Agent 只会漫无目的地游荡" | TodoManager 任务追踪 |
| 5 | 知识加载 | "需要的时候再加载知识，而不是一开始就塞满" | Skill 系统 + 按需加载 |
| 6 | 上下文管理 | "上下文终会溢出，你需要一种腾出空间的方法" | 上下文压缩 + 摘要 |

### Phase 3: DELEGATION — 让 Agent 会分工 (Chapters 7-9)
**Milestone**: 一个能将复杂任务拆解并委派给子智能体的 Agent

| # | Title | Motto | New Capability |
|---|-------|-------|----------------|
| 7 | 子智能体 | "大任务拆小，每个子任务一个干净的上下文" | Subagent 生成 + 结果回收 |
| 8 | 后台任务 | "慢操作放后台，Agent 继续思考" | 异步任务 + 通知队列 |
| 9 | 持久化任务 | "内存里的计划重启就丢了，写到磁盘上" | 文件级任务图 (DAG) |

### Phase 4: COLLABORATION — 让多个 Agent 协作 (Chapters 10-13)
**Milestone**: 一个多智能体团队，能自主领取任务、互相通信、隔离工作

| # | Title | Motto | New Capability |
|---|-------|-------|----------------|
| 10 | 智能体团队 | "当任务太大，一个人搞不定，就找队友" | 持久化队友 + 邮箱通信 |
| 11 | 团队协议 | "队友需要共享的沟通规则" | 请求-响应协议 |
| 12 | 自主智能体 | "队友主动扫描任务板，认领自己能做的" | IDLE/WORK 自主循环 |
| 13 | 工作隔离 | "各自在自己的目录工作，互不干扰" | Worktree + 任务隔离 |

### Phase 5: PRODUCTION — 让 Agent 走向真实世界 (Chapters 14-16)
**Milestone**: 一个可以部署、可观测、安全可控的生产级 Agent 系统

| # | Title | Motto | New Capability |
|---|-------|-------|----------------|
| 14 | 安全与权限 | "能力越大，约束越要明确" | 沙箱 + 权限模型 + 确认机制 |
| 15 | 可观测性 | "看不见的 Agent 不可信" | 日志 + 追踪 + 调试界面 |
| 16 | 从 MiniAgent 到生产 | "你已经理解了原理，现在看看真实世界" | 框架评估 + 架构模式 + 部署策略 |

## Cumulative Capability Table

| Ch | New Capability | Tools | System State After |
|----|---------------|-------|--------------------|
| 1 | Agent 循环 | 1 (bash) | 能执行单条命令 |
| 2 | 工具分发 | 4 (bash, read, write, edit) | 能读写文件 |
| 3 | 多轮对话 | 4 | 能记住上下文，连续工作 |
| 4 | 任务规划 | 5 (+todo) | 能拆解多步任务并追踪进度 |
| 5 | 知识加载 | 6 (+load_skill) | 能按需加载领域知识 |
| 6 | 上下文压缩 | 7 (+compact) | 能处理超长任务不溢出 |
| 7 | 子智能体 | 7 (+task in parent) | 能分派子任务 |
| 8 | 后台任务 | 8 (+bg_run) | 能异步执行慢操作 |
| 9 | 持久化任务图 | 11 (+task CRUD) | 任务重启不丢失，有依赖关系 |
| 10 | 智能体团队 | 14 (+spawn, send, inbox) | 多个 Agent 并行工作 |
| 11 | 团队协议 | 18 (+protocols) | 有序的审批和关闭流程 |
| 12 | 自主领取 | 20 (+idle, claim) | Agent 自主发现和认领任务 |
| 13 | 工作隔离 | 22 (+worktree) | 多 Agent 互不干扰 |
| 14 | 安全权限 | 22 (+sandbox) | 安全沙箱，危险操作需确认 |
| 15 | 可观测性 | 22 (+logging) | 完整的运行追踪和调试 |
| 16 | 生产部署 | — | 理解框架选型和部署架构 |

## Competitive Landscape

| Resource | Type | How This Book Differs |
|----------|------|----------------------|
| 《LangChain in Action》 | Book | 框架教程 vs 从零构建原理 |
| learn-claude-code | Open source | 源码解析 vs 动手构建，本书更面向新手，有完整教学叙事 |
| AutoGen/CrewAI 文档 | Docs | API 参考 vs 理解底层机制 |
| 各类 "Build AI Agent" 博客 | Blog | 通常只到单 Agent，本书覆盖多 Agent 协作 |
| Andrew Ng 的 Agent 课程 | Course | 概念讲解 vs 完整代码实现 |

## Technical Requirements

- **Python version**: 3.10+
- **Key libraries**: anthropic (Claude API) 或 openai (OpenAI API)，无框架依赖
- **Hardware**: 普通笔记本电脑即可，不需要 GPU
- **API Key**: 需要一个 LLM API key（Claude 或 GPT-4）
- **Operating System**: macOS / Linux / WSL (Windows Subsystem for Linux)
