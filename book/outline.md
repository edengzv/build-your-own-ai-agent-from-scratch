# 《智能体入门：从零构建通用 AI Agent》 完整大纲

## 学习路径图

```
Phase 1: THE LOOP                Phase 2: PLANNING
  Ch01 → Ch02 → Ch03              Ch04 → Ch05 → Ch06
  循环    工具    记忆              规划    知识    上下文

Phase 3: DELEGATION              Phase 4: COLLABORATION
  Ch07 → Ch08 → Ch09              Ch10 → Ch11 → Ch12 → Ch13
  子Agent  后台    持久化            团队    协议    自主     隔离

Phase 5: PRODUCTION
  Ch14 → Ch15 → Ch16
  安全    观测    部署
```

---

# Part I: THE LOOP — 让 Agent 动起来

---

## Chapter 1: 你好，Agent

> **Motto**: "一个循环就是全部的开始"

一切从一个 while 循环开始。本章带领读者理解 Agent 的本质——它不是一个复杂的 AI 系统，而是一个简单到令人惊讶的循环：发送消息给 LLM → 检查是否需要调用工具 → 执行工具 → 把结果送回 LLM → 重复。读者将在 30 行代码内拥有一个能执行 bash 命令的 Agent。

### Sections

- **1.1 什么是 AI Agent？** (~800 words)
  从聊天机器人 vs Agent 的区别切入。Agent 的核心特征：自主决策、工具使用、目标导向。不是"更聪明的 ChatGPT"，而是"能动手做事的 AI"。

- **1.2 Agent = Model + Harness** (~600 words)
  引入核心概念：智能来自模型，能力来自 Harness（工具 + 知识 + 观察 + 行动接口 + 权限）。我们要构建的就是 Harness。

- **1.3 环境搭建** (~1,000 words)
  Python 环境、API Key 配置、项目目录初始化。包含 verify_setup.py 脚本。

- **1.4 第一个 Agent 循环** (~2,500 words)
  逐行构建 agent_loop()：消息列表 → LLM 调用 → stop_reason 检查 → 工具执行 → 结果回注。解释每一行为什么存在。

- **1.5 添加 Bash 工具** (~1,500 words)
  定义工具 schema，实现 handle_bash()，注册到 TOOLS 列表。运行第一个任务："列出当前目录的文件"。

- **1.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,000
**Code after chapter**: `agent.py` (~30 lines), 1 tool (bash)

---

## Chapter 2: 工具调用

> **Motto**: "增加一个工具，只需增加一个处理函数"

上一章的 Agent 只会用 bash，什么都要通过 shell 命令完成。本章引入工具分发机制——一个字典映射，让 Agent 能够根据需要选择合适的工具。读者将添加 read_file、write_file、edit_file 三个新工具。

### Sections

- **2.1 The Problem: 一切都是 bash** (~800 words)
  展示上一章的 Agent 用 `cat` 读文件、用 `echo >` 写文件的尴尬。不安全、不可靠、错误处理差。

- **2.2 工具分发映射** (~1,500 words)
  引入 TOOL_HANDLERS 字典。核心模式：`{tool_name: handler_function}`。循环不变，只改分发逻辑。

- **2.3 实现文件操作工具** (~2,500 words)
  逐个实现 read_file、write_file、edit_file。每个工具：schema 定义 → handler 实现 → 测试。

- **2.4 安全路径检查** (~1,200 words)
  引入 safe_path() 函数，限制文件操作在工作目录内。简单但重要的安全边界。

- **2.5 工具设计原则** (~1,000 words)
  好工具的特征：单一职责、清晰的输入/输出 schema、有意义的错误信息、安全边界。

- **2.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,500
**Code after chapter**: `agent.py` (~80 lines), 4 tools (bash, read_file, write_file, edit_file)

---

## Chapter 3: 对话记忆

> **Motto**: "没有记忆的 Agent 和函数调用没有区别"

目前的 Agent 每次运行都是一次性的——执行完就忘记一切。本章让 Agent 拥有多轮对话能力，能够在一次会话中记住之前的交互，像一个真正的助手一样连续工作。

### Sections

- **3.1 The Problem: 健忘的 Agent** (~800 words)
  演示连续两个请求，Agent 不记得第一个请求做了什么。"你刚才创建的文件叫什么？""我不知道你在说什么。"

- **3.2 消息列表就是记忆** (~1,200 words)
  解释 LLM 的"记忆"本质——消息列表。不是什么神奇的记忆系统，就是把历史对话保留在 messages 数组里。

- **3.3 实现交互式 REPL** (~2,000 words)
  将单次执行改为 REPL 循环。用户输入 → 追加到 messages → 调用 agent_loop → 显示结果 → 等待下一轮输入。

- **3.4 系统提示词设计** (~1,500 words)
  引入 system prompt。好的系统提示词：身份定义、能力边界、行为规范。避免过长——为后续 Skill 系统留下伏笔。

- **3.5 消息格式详解** (~1,500 words)
  深入 messages 数组的结构：role(system/user/assistant)、content blocks、tool_use 和 tool_result 的关系。

- **3.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,500
**Code after chapter**: `agent.py` (~120 lines), 4 tools, interactive REPL

---

# Part II: PLANNING — 让 Agent 会思考

> 你已经构建了一个能执行命令、读写文件、记住对话的 Agent。它能处理简单的单步任务。但试试给它一个复杂任务——"重构这个模块并运行测试"——它会迷失方向，跳来跳去，遗漏步骤。
>
> 接下来三章，你将赋予它规划能力、领域知识、以及在有限上下文窗口中生存的能力。

---

## Chapter 4: 任务规划

> **Motto**: "没有计划的 Agent 只会漫无目的地游荡"

一个没有规划能力的 Agent 在面对多步骤任务时表现糟糕——它会跳步、重复、忘记目标。本章引入 TodoManager，让 Agent 能够将复杂任务拆解为步骤并追踪进度。

### Sections

- **4.1 The Problem: 多步任务的混乱** (~800 words)
  给 Agent 一个"创建一个 Python 包，包含 setup.py、README、测试"的任务。观察它如何迷失。

- **4.2 TodoManager 设计** (~1,500 words)
  数据结构：任务列表，每项有 content、status(pending/in_progress/completed)。约束：同一时间只能有一项 in_progress。

- **4.3 实现 todo 工具** (~2,000 words)
  todo 工具的 schema 和 handler。支持 add、update_status、list 操作。

- **4.4 提醒机制** (~1,200 words)
  "Nag reminder"：如果 Agent 连续 3 轮未更新 todo，自动注入 `<reminder>` 消息。引导而非强制。

- **4.5 规划 vs 执行：Agent 的两种模式** (~1,500 words)
  好的 Agent 先规划再执行。讨论 Plan-then-Execute 模式和 Interleaved 模式的取舍。

- **4.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,500
**Code after chapter**: `agent.py` (~180 lines) + `todo.py` (~60 lines), 5 tools

---

## Chapter 5: 知识加载

> **Motto**: "需要的时候再加载知识，而不是一开始就塞满"

把所有领域知识塞进 system prompt 是一种浪费——大部分时候用不上，却占据了宝贵的上下文窗口。本章引入 Skill 系统：两层注入机制，名字和描述在 system prompt 里（每个约 100 tokens），完整内容按需加载。

### Sections

- **5.1 The Problem: 膨胀的系统提示** (~800 words)
  演示把 5000 词的指南塞进 system prompt 后的问题：上下文浪费、注意力稀释、无关知识干扰。

- **5.2 两层注入架构** (~1,500 words)
  Layer 1: skill 目录 + 描述列表注入 system prompt。Layer 2: `load_skill()` 工具按需读取完整 SKILL.md。

- **5.3 Skill 目录结构** (~1,200 words)
  SKILL.md 格式：YAML frontmatter (name, description) + Markdown body。目录约定。

- **5.4 实现 load_skill 工具** (~2,000 words)
  扫描 skills 目录 → 注入摘要到 system prompt → 实现 load_skill handler。

- **5.5 设计好的 Skill** (~1,500 words)
  description 的重要性（Agent 靠它决定何时加载）。简洁原则。渐进式披露。

- **5.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,500
**Code after chapter**: `agent.py` + `skill_loader.py` (~60 lines), 6 tools

---

## Chapter 6: 上下文管理

> **Motto**: "上下文终会溢出，你需要一种腾出空间的方法"

上下文窗口是有限的。读 30 个文件 + 执行 20 条命令 = 超过 10 万 tokens。本章实现三层上下文压缩策略，让 Agent 能够处理任意长度的任务而不崩溃。

### Sections

- **6.1 The Problem: 上下文窗口溢出** (~800 words)
  演示一个长任务中 Agent 突然出错或"失忆"——因为旧消息被截断了。

- **6.2 理解 Token 和上下文窗口** (~1,200 words)
  什么是 token？为什么有上限？不同模型的上下文长度。为什么"更大的窗口"不是答案（注意力稀释）。

- **6.3 第一层：微压缩** (~1,500 words)
  每轮自动执行：将 3 轮以前的 tool_result 替换为 `[tool result: 42 lines, see original]` 占位符。

- **6.4 第二层：自动摘要** (~2,000 words)
  当 token 数超过阈值：保存完整记录到 `.transcripts/`，让 LLM 自己总结，用摘要替换所有消息。

- **6.5 第三层：手动压缩** (~1,200 words)
  compact 工具：Agent 主动决定何时压缩。有时 Agent 比自动策略更知道什么该保留。

- **6.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,200
**Code after chapter**: `agent.py` + `context.py` (~100 lines), 7 tools

---

# Part III: DELEGATION — 让 Agent 会分工

> Agent 现在能规划、能记忆、能加载知识、能管理上下文了。它是一个称职的独立工作者。但给它一个真正复杂的任务——"调研三个竞品的 API，写一份对比报告"——它的上下文会被调研过程塞满，写报告时已经忘了调研细节。
>
> 接下来三章，你将让它学会分工——把子任务交给子智能体，自己只负责协调。

---

## Chapter 7: 子智能体

> **Motto**: "大任务拆小，每个子任务一个干净的上下文"

当 Agent 处理复杂任务时，消息数组越来越长，上下文被各种子任务的细节污染。本章引入子智能体——独立的 Agent 实例，拥有自己的消息列表，完成后只返回精炼的结果摘要。

### Sections

- **7.1 The Problem: 上下文污染** (~800 words)
  演示一个复杂任务中，Agent 的消息列表被子任务细节淹没，主任务推理质量下降。

- **7.2 Subagent 架构** (~1,500 words)
  run_subagent()：新建 messages=[], 运行独立 agent_loop，返回最终文本摘要给父 Agent。干净的上下文隔离。

- **7.3 实现 task 工具** (~2,000 words)
  父 Agent 的 task 工具：接受描述和 prompt，创建子 Agent 执行，收集结果。子 Agent 的工具集不包含 task（防止递归）。

- **7.4 父子 Agent 的工具配置** (~1,200 words)
  父 Agent 有 task 工具但不自己干活；子 Agent 有执行工具但不能再分派。职责边界。

- **7.5 Subagent 模式的局限** (~1,000 words)
  一次性的、无状态的、同步阻塞的。为后续章节（后台任务、持久化队友）埋伏笔。

- **7.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,000
**Code after chapter**: `agent.py` + `subagent.py` (~50 lines), 7 tools (task in parent)

---

## Chapter 8: 后台任务

> **Motto**: "慢操作放后台，Agent 继续思考"

子智能体是同步的——父 Agent 要等子 Agent 完成才能继续。如果一个任务需要运行 `npm install`（30 秒）或 `pytest`（2 分钟），整个 Agent 都在等。本章引入后台任务管理器，让慢操作异步执行。

### Sections

- **8.1 The Problem: 同步阻塞** (~800 words)
  演示 Agent 等待一个长时间运行的测试套件，完全卡住。

- **8.2 BackgroundManager 设计** (~1,500 words)
  daemon 线程 + subprocess + 线程安全通知队列。start() 立即返回，结果通过通知注入。

- **8.3 实现后台执行** (~2,000 words)
  bg_run 工具：启动后台进程。bg_check 工具：检查状态。通知机制：在每次 LLM 调用前 drain 队列，注入 `<background-results>`。

- **8.4 并发控制** (~1,200 words)
  线程安全、资源限制、超时处理。简单但必要的并发管理。

- **8.5 后台 vs 子智能体：何时用哪个** (~1,000 words)
  后台任务：不需要 LLM 推理的慢操作。子智能体：需要 LLM 推理的子问题。

- **8.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,000
**Code after chapter**: `agent.py` + `background.py` (~80 lines), 8 tools

---

## Chapter 9: 持久化任务

> **Motto**: "内存里的计划重启就丢了，写到磁盘上"

Chapter 4 的 TodoManager 是一个内存中的扁平列表——没有任务依赖关系，压缩上下文时会丢失，重启就没了。本章将任务系统升级为文件级的任务图（DAG），支持依赖关系和持久化。

### Sections

- **9.1 The Problem: 丢失的计划** (~800 words)
  演示上下文压缩后 Agent 忘记了自己的 todo 列表。或者重启后一切归零。

- **9.2 文件级任务图设计** (~1,500 words)
  每个任务一个 JSON 文件：`.tasks/{id}.json`，包含 status、blockedBy、owner、description。有向无环图（DAG）。

- **9.3 实现任务 CRUD** (~2,500 words)
  task_create、task_update、task_list、task_get 四个工具。完成一个任务时自动清除下游的 blockedBy。

- **9.4 任务依赖与拓扑排序** (~1,200 words)
  如何定义依赖关系。自动解除阻塞。防止循环依赖。

- **9.5 从 TodoManager 到 TaskGraph** (~1,000 words)
  对比两者。TodoManager 适合简单场景；TaskGraph 是多 Agent 协作的基础（为 Part IV 铺垫）。

- **9.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,500
**Code after chapter**: `agent.py` + `tasks.py` (~120 lines), 11 tools

---

# Part IV: COLLABORATION — 让多个 Agent 协作

> 你的 Agent 现在能规划、能分工、能持久化任务。但子智能体是一次性的——完成就消失，没有身份，没有跨任务的记忆。如果你需要一个"代码审查员"和一个"测试工程师"同时工作呢？
>
> 接下来四章，你将构建一个完整的多智能体团队系统。

---

## Chapter 10: 智能体团队

> **Motto**: "当任务太大，一个人搞不定，就找队友"

子智能体（Ch7）是一次性的——没有身份、没有生命周期、调用完就消失。本章引入持久化队友：有名字、有角色、有自己的 Agent 循环、通过邮箱通信的长期运行的 Agent 实例。

### Sections

- **10.1 The Problem: 一次性的帮手** (~800 words)
  需要一个"审查员"反复检查代码质量。用 subagent 实现：每次都要重新初始化，没有跨任务的经验积累。

- **10.2 持久化队友设计** (~1,500 words)
  生命周期：spawn → WORKING → IDLE → WORKING → ... → SHUTDOWN。每个队友独立线程 + 独立 agent_loop。

- **10.3 邮箱通信系统** (~2,000 words)
  `.team/inbox/{agent_name}.jsonl`。JSONL 格式，append-only。send() 写入目标邮箱，read_inbox() 读取自己的。

- **10.4 实现 spawn/send/inbox 工具** (~2,000 words)
  Lead Agent 的三个新工具。Teammate 的工具集配置。

- **10.5 Lead vs Teammate 的角色分工** (~1,000 words)
  Lead 负责规划和协调，Teammate 负责执行。权限差异。

- **10.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,800
**Code after chapter**: `agent.py` + `team.py` (~150 lines), 14 tools

---

## Chapter 11: 团队协议

> **Motto**: "队友需要共享的沟通规则"

队友能通信了，但缺乏结构化的协调。如何安全地关闭一个队友？如何让队友提交方案等待审批？本章引入请求-响应协议，为团队通信添加秩序。

### Sections

- **11.1 The Problem: 无序的通信** (~800 words)
  Lead 发送"停止"消息，但 Teammate 正在执行中间状态——直接停止会导致数据损坏。

- **11.2 请求-响应协议** (~1,500 words)
  request_id + status FSM (pending → approved | rejected)。通用模式，可用于任何需要确认的场景。

- **11.3 关闭协议** (~1,500 words)
  Lead 发送 shutdown_request → Teammate 完成当前工作 → 响应 approve → 安全退出。

- **11.4 方案审批协议** (~1,500 words)
  Teammate 提交 plan_request → Lead 审查 → approve/reject + 反馈。

- **11.5 实现协议工具** (~2,000 words)
  shutdown_req, shutdown_resp, plan_req, plan_resp 四组工具的实现。

- **11.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,800
**Code after chapter**: `agent.py` + `protocols.py` (~100 lines), 18 tools

---

## Chapter 12: 自主智能体

> **Motto**: "队友主动扫描任务板，认领自己能做的"

到目前为止，队友只在被明确指示时才工作。Lead 必须手动分配每一个任务。本章让队友变得自主——在空闲时扫描任务板，认领自己能做的任务，超时后自动关闭。

### Sections

- **12.1 The Problem: 被动的队友** (~800 words)
  Lead 忙于分配任务而不是思考策略。队友闲着也不会主动找事做。

- **12.2 IDLE/WORK 循环** (~1,500 words)
  IDLE 阶段：每 5 秒轮询——检查邮箱、扫描 `.tasks/` 中的 unclaimed 任务。找到就认领（切换到 WORK），60 秒超时就自动关闭。

- **12.3 任务认领机制** (~2,000 words)
  claim_task()：原子操作设置 task.owner + 状态更新。冲突处理：两个 Agent 同时认领。

- **12.4 身份恢复** (~1,200 words)
  上下文压缩后 Agent 忘记自己是谁。身份重注入：在压缩后的摘要开头添加角色描述。

- **12.5 自主的边界** (~1,000 words)
  完全自主 vs 受控自主。什么任务应该自主认领，什么需要 Lead 审批。

- **12.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,000
**Code after chapter**: `agent.py` + `autonomous.py` (~80 lines), 20 tools

---

## Chapter 13: 工作隔离

> **Motto**: "各自在自己的目录工作，互不干扰"

多个 Agent 在同一目录工作 = 灾难。两个 Agent 同时编辑同一个文件会互相覆盖。本章引入 Git Worktree 绑定任务的机制，每个 Agent 在自己的独立工作目录中操作。

### Sections

- **13.1 The Problem: 文件冲突** (~800 words)
  两个 Agent 同时修改 `app.py`——一个的修改被另一个覆盖。

- **13.2 控制面 vs 执行面** (~1,500 words)
  控制面：`.tasks/` 存储目标和状态。执行面：`.worktrees/` 提供隔离的工作目录。

- **13.3 Git Worktree 入门** (~1,500 words)
  什么是 worktree。git worktree add/remove。为什么比复制目录好。

- **13.4 实现 Worktree 绑定** (~2,000 words)
  创建 worktree → 绑定到 task_id → Agent 在 worktree 中工作 → 完成后合并/删除。

- **13.5 事件流** (~1,200 words)
  `.worktrees/events.jsonl` 记录生命周期事件。状态机：absent → active → removed | kept。

- **13.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,500
**Code after chapter**: `agent.py` + `worktree.py` (~100 lines), 22 tools

---

# Part V: PRODUCTION — 让 Agent 走向真实世界

> 你已经构建了一个功能完备的多智能体系统。它能规划、能分工、能协作、能隔离。但它还缺少三样东西才能走向生产：安全保障、可观测性、以及对真实世界复杂性的应对策略。

---

## Chapter 14: 安全与权限

> **Motto**: "能力越大，约束越要明确"

一个能执行 bash 命令的 Agent 可以做任何事——包括 `rm -rf /`。本章构建安全层：路径沙箱、命令白名单、危险操作确认机制、权限模型。

### Sections

- **14.1 The Problem: 不受约束的能力** (~800 words)
  Agent 执行了一个破坏性命令的场景。或者读取了不该读的文件。

- **14.2 沙箱模型** (~1,500 words)
  工作目录限制、路径遍历防护、环境变量隔离。扩展 Chapter 2 的 safe_path()。

- **14.3 权限分级** (~1,500 words)
  工具级别的权限：read-only、write、execute、dangerous。不同角色的 Agent 拥有不同权限。

- **14.4 人类确认机制** (~2,000 words)
  危险操作前暂停，请求人类确认。交互式审批流程。自动化 vs 人在环中的平衡。

- **14.5 Prompt 注入防御** (~1,200 words)
  什么是 prompt injection。基本防御：输入消毒、输出验证、角色边界。

- **14.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,500
**Code after chapter**: `agent.py` + `security.py` (~120 lines), 22 tools + sandbox layer

---

## Chapter 15: 可观测性

> **Motto**: "看不见的 Agent 不可信"

Agent 在"黑箱"中运行——你不知道它在想什么、为什么选择这个工具、为什么这一步花了 30 秒。本章添加结构化日志、执行追踪、token 使用统计，让 Agent 的行为完全可观测。

### Sections

- **15.1 The Problem: 黑箱 Agent** (~800 words)
  Agent 失败了，但你不知道是在哪一步、为什么失败。

- **15.2 结构化日志** (~1,500 words)
  JSON 格式日志。每次 LLM 调用、工具执行、决策点都记录。日志级别设计。

- **15.3 执行追踪** (~2,000 words)
  Trace ID 贯穿整个 Agent 循环。父子 Agent 的 trace 关联。trace 可视化。

- **15.4 Token 经济学** (~1,200 words)
  每次 LLM 调用的 token 消耗统计。成本估算。发现上下文浪费。

- **15.5 调试技巧** (~1,500 words)
  常见问题的诊断方法：Agent 循环不停、工具反复调用、输出质量下降。

- **15.6 What Changed / Try It Yourself / Summary** (~1,500 words)

**Estimated words**: ~8,500
**Code after chapter**: `agent.py` + `observability.py` (~100 lines)

---

## Chapter 16: 从 MiniAgent 到生产

> **Motto**: "你已经理解了原理，现在看看真实世界"

本书的最后一章不写代码——而是带领读者审视真实世界的 Agent 系统。用你已经掌握的概念去理解 LangChain、AutoGen、CrewAI、Claude Code 的设计决策，并讨论将 MiniAgent 部署到生产环境的策略。

### Sections

- **16.1 MiniAgent 回顾** (~1,500 words)
  16 章构建的完整系统架构图。每个组件的作用。约 2,000 行代码的全景。

- **16.2 真实世界的 Agent 框架** (~2,500 words)
  用 MiniAgent 的概念映射到 LangChain (tools/chains)、AutoGen (multi-agent)、CrewAI (teams)、Claude Code (harness)。你已经理解了它们的核心。

- **16.3 部署架构模式** (~2,000 words)
  CLI Agent、API Agent、Event-driven Agent。进程管理、状态持久化、横向扩展。

- **16.4 成本控制** (~1,200 words)
  token 优化策略。缓存。模型选择（大模型思考、小模型执行）。

- **16.5 Agent 的未来** (~1,500 words)
  从工具使用到环境交互。从单模态到多模态。从辅助到自主。保持务实。

- **16.6 总结与下一步** (~1,200 words)
  读者的成长路径。推荐的进阶资源。社区。

**Estimated words**: ~10,000
**Code after chapter**: — (回顾章)

---

## Appendices

### Appendix A: LLM API 快速参考
- OpenAI Chat Completion API 格式
- Anthropic Messages API 格式
- Tool/function calling schema 对照表

### Appendix B: MiniAgent 完整代码索引
- 按模块列出所有文件和关键函数
- 每个文件的用途说明

### Appendix C: 常见问题排查
- Agent 循环不终止
- Token 超限
- 工具调用格式错误
- 多 Agent 死锁

---

## 全书统计

| Metric | Value |
|--------|-------|
| Chapters | 16 |
| Phases | 5 |
| Estimated total words | ~136,000 |
| Tools at completion | 22+ |
| Final codebase | ~2,000 lines Python |
