# Skill 工程 — 完整大纲

## Learning Dependency Graph

```
Ch01 (Skill 基础) ──→ Ch02 (Description) ──→ Ch03 (指令写作)
                                                    │
                     ┌──────────────────────────────┘
                     ↓
               Ch04 (Multi-Pass) ──→ Ch05 (命令路由) ──→ Ch06 (模板锚定)
                                                              │
                     ┌────────────────────────────────────────┘
                     ↓
               Ch07 (三层架构) ──→ Ch08 (多工具编排) ──→ Ch09 (质量自检)
                                                              │
                     ┌────────────────────────────────────────┘
                     ↓
               Ch10 (测试调优) ──→ Ch11 (案例解剖) ──→ Ch12 (元技能)
```

---

## Phase 1: FIRST SKILL — 写出你的第一个 Skill

### Chapter 1: 你好，Skill

> **Motto**: "一个 SKILL.md 文件就是全部的开始"

**Summary**: 本章从零开始，解释什么是 Skill、为什么需要它、它和 Prompt / System Prompt / MCP 有什么区别。读者将在 5 分钟内写出第一个可工作的 Skill，并观察 Agent 如何发现和加载它。

**Sections**:

- **1.1 为什么需要 Skill** (~800 words)
  - 重复告诉 Agent 同样的话是一种浪费
  - Skill = 可复用的专家知识包
  - Skill 不是工具——工具执行原子操作，Skill 编码"解决问题的策略"（来自学术综述 arxiv.org/abs/2602.12430）

- **1.2 Skill vs Prompt vs System Prompt vs MCP** (~600 words)
  - 对比表：适用场景、持久性、加载机制
  - Skill 的独特定位：可复用的程序化知识
  - 新增 "Tool" 列到对比表：Tool = 原子操作, Skill = 策略性知识包

- **1.3 SKILL.md 的最小结构** (~500 words)
  - YAML Frontmatter: name + description
  - Markdown Body: 指令正文
  - 最小可行示例：10 行 `quick-fix` Skill

- **1.4 安装你的第一个 Skill** (~600 words)
  - 目录位置：`~/.claude/skills/` / `~/.qoder/skills/`
  - 文件系统约定：目录名 = Skill 名
  - 验证：Agent 是否识别到了

- **1.5 Skill 的生命周期** (~800 words)
  - Layer 1: 扫描目录，name + description 注入上下文（~100 tokens）
  - Layer 2: Agent 决定加载，SKILL.md 正文进入对话（~5000 tokens）
  - Layer 3: 按需加载 scripts/ 和 reference/
  - ASCII 图解三层加载流程

- **1.6 Try It Yourself** (~400 words)
  - Verify: 创建 `quick-fix` Skill，让 Agent 修一个简单 Bug
  - Extend: 把 Skill 的 description 改得更模糊，观察 Agent 是否还会加载
  - Explore: 列出你工作中最常对 Agent 重复的 3 件事，哪些适合做成 Skill？

**Estimated word count**: ~3,900

---

### Chapter 2: Description：最重要的一行

> **Motto**: "Agent 看不到你的 Skill 内容，只看到 description"

**Summary**: description 字段决定了 Agent 何时加载你的 Skill——加载时机错误，Skill 再好也白费。本章深入分析 description 的工作原理，通过对比好/坏 description 的实验，教读者写出精准的触发条件。

**Sections**:

- **2.1 description 的工作原理**
- **2.2 好的 description vs 坏的 description** (5 组对比)
- **2.3 三步写 description 法** (What → When → How)
- **2.4 Description 的隐形陷阱：欠触发问题** *[NEW]*
  - Anthropic 发现模型倾向于不触发 Skill（under-triggering）
  - "Pushy" 策略：description 要比直觉更宽泛
  - 何时 Pushy，何时保守的决策表
- **2.5 案例：code-review 的 description 三版演进** (v1→v2→v3)
- **2.6 Karpathy 的 description 哲学**
- **2.7 常见的 description 反模式** (5 种)
- **2.8 一个 description 检查清单**
- **2.9 预告：自动化 Description 优化** *[NEW]*
  - 指向 Ch10.4 的完整 Description 优化循环
- Try It Yourself / Summary / Further Reading

**Estimated word count**: ~6,200

---

### Chapter 3: 可执行的指令

> **Motto**: "模糊的指令产生模糊的结果"

**Summary**: description 让 Skill 被正确加载，但 Skill 正文的指令质量决定了 Agent 执行得好不好。本章对比"模糊指令"和"可执行指令"，教读者用结构化方式写出 Agent 能直接照做的指令。

**Sections**:

- **3.1 为什么 Agent 执行得不好** (~600 words)
  - 常见抱怨："Agent 没按我想的来"
  - 根本原因：你的指令不够精确，Agent 只好猜

- **3.2 模糊指令 vs 可执行指令** (~1200 words)
  - 案例对比：同一个任务的两种写法
  - 模糊："审查代码时注意各种问题，给出适当的建议"
  - 可执行：分步骤、有格式、有具体检查项
  - 可执行性光谱：自然语言 → 伪代码 → 精确模板 → 脚本

- **3.3 结构化指令的五个要素** (~1500 words)
  - **角色声明**：告诉 Agent 它扮演什么角色
  - **步骤序列**：编号的步骤，每步一个动作
  - **输出格式**：明确的模板或示例
  - **约束条件**：边界和限制（"不要..."、"最多..."）
  - **判断标准**：告诉 Agent 怎么判断自己做得好不好
  - **侧栏：LangGPT 的 Role-Skills-Constraints 框架**（~350 words）
    - 对照表：LangGPT 的 Role ≈ 角色声明, Constraints ≈ 约束条件, Workflows ≈ 步骤序列
    - 关键教训：多个独立框架殊途同归——结构化指令优于自由格式
    - 来源：LangGPT (arxiv.org/abs/2402.16929)

- **3.4 实战：从模糊到精确改写 commit-message Skill** (~1200 words)
  - v1（模糊）：20 行 → 效果不稳定
  - v2（结构化）：50 行 → 效果显著提升
  - 逐行分析：每个改进点为什么有效

- **3.5 指令粒度的选择** (~800 words)
  - 低脆弱度任务：高自由度（创意写作）
  - 中脆弱度任务：中自由度（伪代码 + 模板）
  - 高脆弱度任务：低自由度（精确脚本）
  - 如何判断你的任务属于哪个级别

- **3.6 避免的反模式** (~1000 words)
  - **规则堆砌**（首要反模式）：用 ALWAYS/NEVER 大写替代解释原因
    - Anthropic 洞察："If you find yourself writing ALWAYS or NEVER in all caps, that's a yellow flag"
    - 原理：LLM 有 theory-of-mind，理解 why 后能泛化；只有规则时只能机械遵循
    - 前后对比：`ALWAYS use semicolons` vs `We use semicolons because our linter requires them...`
    - 来源：Anthropic Skill-Creator Research Section 四.1
  - 过度解释基础知识（Agent 已经知道 Python 语法）
  - 重复 Agent 内置能力（不需要教它如何读文件）
  - 写作文而不是写指令

- **3.7 Try It Yourself** (~400 words)
  - Verify: 用改写后的 `commit-message` Skill 生成 5 条提交信息，对比质量
  - Extend: 选一个你工作中常用的流程，写成结构化指令
  - Explore: 给同一个 Skill 写"高自由度"和"低自由度"两个版本，对比输出

**Estimated word count**: ~7,050

---

## Phase 2: CORE CRAFT — 核心写作技巧

### Chapter 4: 多步工作流

> **Motto**: "把大象装进冰箱需要三步，好的 Skill 也是"

**Summary**: 简单的 Skill 只有一组指令。但复杂任务——写文档、做审查、创建项目——需要多个步骤按序执行，每步验证后再进入下一步。本章教你设计 Multi-Pass 工作流，让 Skill 像工厂流水线一样可靠。

**Sections**:

- **4.1 单次执行的局限** (~600 words)
  - 让 Agent 一次性写完一篇 API 文档——结果不可控
  - 根本问题：太多自由度 + 没有检查点

- **4.2 Multi-Pass 模式** (~1000 words)
  - 核心思想：分步执行，每步有明确输入/输出
  - 类比：编译器的 Lexer → Parser → CodeGen 管线
  - Pass 之间的"交接物"（artifact）

- **4.3 设计你的第一个 Multi-Pass Skill** (~1500 words)
  - `api-doc-writer` Skill 的 3-Pass 设计
  - Pass 1: 分析代码结构，输出函数/类列表
  - Pass 2: 为每个函数生成文档
  - Pass 3: 整合、格式化、添加目录
  - 每步之间的暂停点和用户确认

- **4.4 Pass 设计原则** (~800 words)
  - 每个 Pass 只做一件事
  - Pass 之间有明确的交接文件
  - 关键 Pass 后暂停等待用户确认
  - Pass 数量不要超过 5 个

- **4.5 五种工作流设计模式** (~1200 words)
  - **清单式推进**：线性步骤执行。案例：`client-flow`（7 步入职）
  - **诊断-修复-验证**：问题解决模式。案例：`emergency-rescue`（20+ 场景统一模式）
  - **循环反馈**：执行 → 评判 → 重试。案例：`checkmate`（Worker/Judge 架构）
  - **条件分支**：意图路由到不同流程。案例：`anti-pattern-czar`（5 种模式）
  - **量化决策矩阵**：打分 → 阈值 → 行动。案例：`adaptive-reasoning`
  - 与 Multi-Pass 的关系：模式 1-3 是 Multi-Pass 的变体；模式 4-5 是位于 Multi-Pass 之上的路由模式
  - 选择指南：帮助读者判断任务适合哪种模式
  - 来源：OpenClaw Skills Research + Best Practices

- **4.6 案例解剖：wechat-article-writer 的 5-Pass 工作流** (~1200 words)
  - 素材分析 → 洞察综合 → 正文撰写 → 配图制作 → 微信适配
  - 为什么每个 Pass 不能合并
  - 用户确认点的设计

- **4.7 Try It Yourself** (~400 words)
  - Verify: 用 `api-doc-writer` 为一个真实模块生成文档
  - Extend: 把 Ch3 的 `commit-message` 改写成 2-Pass 版本
  - Explore: 你的工作中有什么多步骤流程可以做成 Multi-Pass Skill？

**Estimated word count**: ~6,700

---

### Chapter 5: 命令与路由

> **Motto**: "一个 Skill 多种用法，由命令来切换"

**Summary**: 到目前为止，每个 Skill 只做一件事。但真实场景中，一个领域的 Skill 可能需要多种操作模式——创建 vs 审查 vs 更新。本章教你设计命令表，让一个 Skill 像 CLI 工具一样提供多个子命令。

**Sections**:

- **5.1 为什么需要命令** (~600 words)
  - 问题：写了 3 个相关但分散的 Skill，Agent 不知道该用哪个
  - 解决：合并为一个 Skill，通过命令路由

- **5.2 命令表设计** (~1000 words)
  - Markdown 表格格式：`| Command | Purpose |`
  - 命令命名规范：`/skill-name verb [argument]`
  - 默认命令 vs 显式命令

- **5.3 实战：project-scaffold Skill** (~1500 words)
  - `/project-scaffold create <type>`: 创建新项目
  - `/project-scaffold add <component>`: 添加组件
  - `/project-scaffold config`: 查看/修改配置
  - 命令路由的实现：在 SKILL.md 中如何组织多命令指令

- **5.4 命令设计的原则** (~800 words)
  - 动词优先：create, add, update, delete, check, list
  - 正交性：每个命令做一件不同的事
  - 可发现性：命令名应该自解释
  - 参数设计：必选 vs 可选，默认值
  - 路由应考虑用户状态（模糊想法 vs 明确问题 vs 恢复上下文），而非仅匹配关键词

- **5.5 案例解剖：tech-book-writer 的 14 个命令** (~1000 words)
  - plan → outline → draft → review → consistency → glossary → ...
  - 命令之间的工作流关系
  - 为什么这么多命令而不是拆成多个 Skill

- **5.6 Try It Yourself** (~400 words)
  - Verify: 运行 `project-scaffold` 的不同命令
  - Extend: 给 Ch4 的 `api-doc-writer` 添加 `update` 命令
  - Explore: 分析一个你常用的 CLI 工具（如 git），它的命令设计有什么值得 Skill 借鉴的？

**Estimated word count**: ~5,400

---

### Chapter 6: 模板与示例

> **Motto**: "一个好的示例胜过十段解释"

**Summary**: 指令告诉 Agent "做什么"，但模板和示例告诉它"做成什么样"。本章教你用输入/输出示例、Markdown 模板、代码模板来锚定 Agent 的行为，消除输出的不确定性。

**Sections**:

- **6.1 为什么需要示例** (~600 words)
  - "生成单元测试"——每次输出格式都不一样
  - 示例是最强的行为锚定手段

- **6.2 三种锚定方式** (~1200 words)
  - **输入/输出示例**：Given this input → Produce this output
  - **输出模板**：固定格式，变量部分用占位符
  - **反例**：错误的输出 + 为什么错

- **6.3 实战：test-writer Skill** (~1500 words)
  - 展示一个输入函数 → 期望的测试代码
  - 模板：测试文件结构、命名规范、断言模式
  - 反例："不要生成这种测试"——过度 mock、无断言、测试实现而非行为

- **6.4 示例设计的原则** (~800 words)
  - 代表性：覆盖典型场景，不只是 hello world
  - 多样性：展示 2-3 个不同复杂度的示例
  - 差异性：示例之间应该展示不同的决策路径
  - 简洁性：示例越短越好，只保留教学必需的部分
  - DSPy 的洞察：指令和示例应**联合优化**，而非分开调整——改变指令后示例也需要重选（详见 Ch10）

- **6.5 案例解剖：Karpathy 的 Skill 中的示例使用** (~800 words)
  - 分析 Karpathy 风格 Skill 中如何用最少的示例锚定行为
  - 关键洞察：不是给更多示例，而是给更好的示例

- **6.6 案例解剖：wechat-tech-card 的模板系统** (~1000 words)
  - 5 种卡片类型 × 5 个 HTML 模板
  - 模板变量的设计
  - 品牌配置系统如何与模板集成

- **6.7 Try It Yourself** (~400 words)
  - Verify: 用 `test-writer` 为一个真实函数生成测试
  - Extend: 给 `commit-message` Skill 添加 3 个示例
  - Explore: 取一个输出不稳定的 Skill，通过加示例来锚定它

**Estimated word count**: ~6,400

---

## Phase 3: ARCHITECTURE — 高级架构模式

### Chapter 7: 渐进式加载

> **Motto**: "上下文是公共资源，每个 Token 都很宝贵"

**Summary**: 随着 Skill 越来越复杂，把所有内容塞在一个 SKILL.md 里会带来两个问题：文件太长、加载后吃掉大量上下文。本章教你设计三层架构：SKILL.md 是入口，scripts/ 放确定性逻辑，reference/ 放参考资料。

**Sections**:

- **7.1 一个文件的极限** (~600 words)
  - 当 SKILL.md 超过 500 行会发生什么
  - Token 经济学：一个 500 行 Skill 约占 5000 tokens
  - 问题：挤占了对话中真正有价值的上下文空间

- **7.2 三层架构** (~1200 words)
  - Layer 1: SKILL.md — 核心指令和路由（< 500 行）
  - Layer 2: scripts/ — 确定性计算（Python/Bash 脚本）
  - Layer 3: reference/ — 参考文档、API 规范、样式指南
  - 什么放 SKILL.md，什么放 scripts/，什么放 reference/
  - 引用语法：`[style-guide.md](style-guide.md)` 和 `Study [file](file) for details`
  - **高亮 Callout："Layer 3 的秘密"**——scripts/ 中的脚本可直接执行，**不加载进上下文**。只有脚本的输出进入对话，源码不占 token
  - 设计含义：任何确定性逻辑应该是脚本，而不是自然语言指令
  - 来源：Anthropic Skill System Specification

- **7.3 实战：refactor-guide Skill** (~1500 words)
  - SKILL.md: 重构流程指令（200 行）
  - scripts/analyze_complexity.py: 代码复杂度分析脚本
  - reference/refactoring-patterns.md: 重构模式参考手册
  - 三者如何协同工作

- **7.4 scripts/ 目录设计** (~1000 words)
  - 何时用脚本：确定性计算、数据转换、文件处理
  - 脚本规范：JSON 输出到 stdout，debug 信息到 stderr
  - 输入验证和错误处理
  - Python vs Bash 的选择
  - **7.4.1 脚本优先原则 (Scripts-First)** (~300 words)
    - 判断规则："如果你发现自己在 SKILL.md 里写的算法指令每次执行都一样，提取为脚本"
    - Anthropic 观察："如果 3 次测试运行都独立写出了类似的辅助脚本，那就应该 bundle 它"
    - 脚本编写标准：`set -e`、stderr 用于状态、stdout 用于 JSON 输出
    - 来源：Anthropic Skill-Creator Research

- **7.5 reference/ 目录设计** (~800 words)
  - 何时用参考文档：API 规范、风格指南、检查清单
  - 文档的粒度：每个文件一个主题
  - 引用方式：在 SKILL.md 中用 `Study [file](file)` 引导 Agent

- **7.6 案例解剖：tech-book-writer 的三层架构** (~1200 words)
  - SKILL.md (500 行): 命令路由 + 核心指令
  - progressive-methodology.md: 渐进式方法论
  - illustration-guide.md: 插图系统
  - bilingual-guide.md: 双语支持
  - templates/: 模板文件
  - scripts/: 构建脚本
  - 架构决策：为什么这样拆分

- **7.7 Try It Yourself** (~400 words)
  - Verify: 构建 `refactor-guide` Skill，测试三层协同
  - Extend: 把 Ch6 的 `test-writer` 重构为三层架构
  - Explore: 哪些内容适合放 reference/ 而不是 SKILL.md？写出你的判断标准

**Estimated word count**: ~7,200

---

### Chapter 8: 多工具编排

> **Motto**: "Skill 的力量不在文字，在于它能调动的工具"

**Summary**: 到目前为止，Skill 主要是"知识"——告诉 Agent 怎么做。但强大的 Skill 还能指导 Agent 使用特定工具的组合：先用 Bash 检查环境，再用 Read 读取配置，最后用 WebFetch 验证。本章教你在 Skill 中编排多工具协作。

**Sections**:

- **8.1 工具是 Skill 的手和脚** (~600 words)
  - 知识型 Skill vs 行动型 Skill
  - 行动型 Skill 需要明确的工具使用指南

- **8.2 工具声明与使用指南** (~1000 words)
  - Tool Usage 表格模式：`| Tool | Purpose |`
  - 何时声明工具：不是列出所有可用工具，而是列出 Skill 需要的工具
  - 工具使用顺序的暗示

- **8.3 实战：deploy-checker Skill** (~1500 words)
  - 工具编排：Bash(check env) → Read(config) → Bash(run tests) → WebFetch(health check)
  - 条件分支：测试失败时的处理流程
  - 并行 vs 串行：哪些步骤可以并行

- **8.4 编排模式** (~1200 words)
  - **管线模式**：A → B → C，前一步的输出是后一步的输入
  - **扇出模式**：一个步骤触发多个并行步骤
  - **条件模式**：根据中间结果选择不同路径
  - **循环模式**：重复执行直到满足条件
  - 前瞻：Promptfoo 的 `trajectory:tool-sequence` 和 `trajectory:step-count` 断言可验证编排行为是否正确（详见 Ch10 §10.2 断言分类体系）

- **8.5 案例解剖：wechat-article-writer 的工具编排** (~1000 words)
  - WebFetch 抓取 → 分析综合 → Write 输出 → ImageGen 配图 → show_widget 预览
  - 工具失败时的降级策略
  - AskUserQuestion 在管线中的角色

- **8.6 Try It Yourself** (~400 words)
  - Verify: 用 `deploy-checker` 检查一个真实项目的部署就绪状态
  - Extend: 给 `api-doc-writer` 添加工具编排（Read 源码 → Write 文档）
  - Explore: 设计一个需要 3 种以上工具的 Skill 场景

**Estimated word count**: ~5,800

---

### Chapter 9: 质量检查清单

> **Motto**: "好的 Skill 自己知道自己做得好不好"

**Summary**: 优秀的 Skill 不仅告诉 Agent 做什么，还告诉它如何验证自己的输出。内置 Quality Checklist 让 Agent 在输出前自检，大幅提升结果的一致性和质量。

**Sections**:

- **9.1 为什么需要自检** (~600 words)
  - 没有自检的 Skill：输出质量靠运气
  - 有自检的 Skill：Agent 会在输出前过一遍清单
  - 类比：飞行员的起飞前检查清单

- **9.2 Quality Checklist 设计** (~1200 words)
  - Markdown 复选框格式：`- [ ] 检查项`
  - 检查项的分类：内容质量、格式规范、约束遵守
  - 检查项的粒度：可验证的具体条件，不是模糊的"质量好"
  - 检查清单放在 SKILL.md 的什么位置
  - **9.2.1 Anti-Patterns 清单：告诉 Agent 不该做什么** (~400 words)
    - 防御性设计哲学："告诉 Agent 不该做什么往往比告诉它该做什么更重要"
    - 结构：❌ 反模式 + 原因 + ✅ 修正
    - 案例：OpenClaw `agent-self-reflection` 的 5 个 ❌ 反模式
    - OpenClaw 10 大反模式作为"负面清单"模板
    - 来源：OpenClaw Best Practices

- **9.3 实战：pr-reviewer Skill 的双重检查** (~1500 words)
  - 输出质量检查：审查报告是否覆盖所有维度
  - 自身行为检查：是否遗漏了重要文件、是否有误报
  - 两级清单的设计

- **9.4 从检查清单到评分系统** (~1100 words)
  - 简单检查：通过 / 不通过
  - 加权评分：不同检查项不同权重
  - 分数阈值：低于 X 分需要重做
  - 何时用检查清单，何时用评分系统
  - **加权断言实践**：安全检查 weight 3, 命名规范 weight 1, 测试覆盖 weight 2
  - 阈值组：80% 的质量检查通过才批准
  - 来源：Promptfoo weighted assertions

- **9.5 确认偏误与隔离验证** (~800 words)
  - 自检最大敌人：**确认偏误**——创建输出的 Agent 倾向于确认它是正确的
  - EvoSkills 突破：Generator 和 Verifier 信息隔离 → 性能从 32% 跳到 75%
  - 实践技巧：
    - 让 Agent 只看输出（不看生成过程）再检查
    - 用独立的子 Agent 做验证
    - 框架化为"你在审查别人的工作"
  - 与 Ch12 的联系：skill-creator 的 Comparator Agent 也采用信息隔离（盲比较）
  - 来源：EvoSkills (arxiv.org/html/2604.01687v1)

- **9.6 案例解剖：每个优秀 Skill 的检查清单** (~1200 words)
  - wechat-article-writer 的 16 项自检
  - douyin-video-creator 的分类检查
  - tech-book-writer 的 20+ 项 review checklist
  - 共同模式总结

- **9.7 Try It Yourself** (~400 words)
  - Verify: 给 `pr-reviewer` 一个有问题的 PR，观察自检效果
  - Extend: 给 Ch6 的 `test-writer` 添加 8 项质量清单
  - Explore: 回顾你之前写的所有 Skill，哪些最需要加上自检？
  - 新练习：构建你自己的 Pre-Launch Checklist，参考 OpenClaw 20 项检查清单模板

**Estimated word count**: ~7,400

---

## Phase 4: MASTERY — 从技巧到精通

### Chapter 10: 测试与调优

> **Motto**: "写完不是终点，验证才是"

**Summary**: 一个 Skill 写出来后，怎么知道它好不好？本章教你建立评估方法论：设计测试用例、对比 A/B 版本、收集使用反馈、持续迭代。

**Sections**:

- **10.1 Skill 的质量维度** (~800 words)
  - 触发准确性：该加载时加载，不该时不加载
  - 执行一致性：同样的输入，输出质量稳定
  - 输出质量：满足用户期望
  - Token 效率：用最少的 tokens 达到效果

- **10.2 设计测试用例** (~1300 words)
  - 正向测试：给正确的输入，期望正确的输出
  - 边界测试：极端情况（空输入、超长输入）
  - 负向测试：不应该触发时是否正确地不触发
  - 测试用例模板
  - **合成测试生成**：用 LLM 生成多样化测试场景，人工审核后使用；EvoSkills 的方法：自动生成合成断言（来源：EvoSkills + Skill-Optimizer）
  - 注意：合成数据是 bootstrap 手段，不替代人工判断

- **10.3 A/B 版本对比** (~1200 words)
  - 修改一个变量，对比两个版本的输出
  - A/B 测试的三个维度：description、指令、模板
  - 记录和分析实验结果

- **10.4 Description 自动化优化** (~800 words)
  - 系统方法：生成 20 个评估查询（8-10 should-trigger + 8-10 should-not-trigger）
  - 关键设计：should-not-trigger 必须是**近似误匹配**，非明显无关
  - 60/40 训练/测试集分割防止过拟合
  - 每查询运行 3 次确保统计可靠性
  - 最多 5 轮迭代，按**测试集**分数选最佳（避免训练集过拟合）
  - 深层洞察："Agent 只在自己无法独立完成时才会咨询 Skill"——简单请求不会触发任何 Skill
  - 来源：Anthropic Skill-Creator Research（description optimization loop）

- **10.5 断言体系：三层验证** (~1000 words)
  - **Layer 1 确定性断言**（机器可检查，无需 LLM）：`contains`, `equals`, `is-json`, `is-html`, cost/latency 阈值
  - **Layer 2 Agent 专用断言**（Skill 测试特有）：`skill-used`（是否触发了 Skill）, `trajectory:tool-sequence`（工具调用顺序）, `trajectory:step-count`（执行步数）, `trajectory:goal-success`（是否达成目标）
  - **Layer 3 模型辅助断言**（LLM 评判 LLM 输出）：`llm-rubric`（自定义评分标准）, `factuality`（事实性）, `answer-relevance`（相关性）, `similar`（语义相似度）
  - 测试金字塔：大量 L1（快/便宜）, 一些 L2（Skill 专用）, 少量 L3（贵但全面）
  - A/B 方法论：with-skill vs baseline 并行运行对比
  - 来源：Promptfoo 断言体系 + Anthropic Skill-Creator 评估框架

- **10.6 四维诊断与饱和曲线** (~800 words)
  - SkillForge 四维度并行诊断框架：
    1. **知识**：Skill 是否包含正确的领域知识？
    2. **工具使用**：是否正确编排工具？
    3. **澄清策略**：输入模糊时是否追问？
    4. **语气风格**：输出是否匹配预期的沟通风格？
  - 并行诊断：每个维度独立分析，然后优先级排序修复
  - **饱和曲线**：知识修复 2-3 轮后收益递减，工具/风格持续改进
  - 决策规则：连续两轮测试集改进 <2% 时停止迭代
  - 来源：SkillForge (arxiv.org/html/2604.08618v1)

- **10.7 跨模型测试** (~800 words)
  - 不同模型对 Skill 的理解差异
  - Haiku vs Sonnet vs Opus 的表现差异
  - 为什么要针对目标模型优化

- **10.8 迭代循环** (~600 words)
  - 收集使用中的问题
  - 分析根因：description 问题还是指令问题？
  - 修改 → 测试 → 部署 的循环

- **10.9 版本管理** (~600 words)
  - 用 Git 管理 Skill 版本
  - CHANGELOG 的写法
  - 回滚策略

- **10.10 Try It Yourself** (~400 words)
  - Verify: 对你写过的任一 Skill 做 5 次测试，记录输出一致性
  - Extend: 创建一个 Skill 的 A/B 版本，对比 description 的改动效果
  - Explore: 同一个 Skill 在不同 AI 工具中的表现差异

**Estimated word count**: ~8,300

---

### Chapter 11: 案例解剖室

> **Motto**: "最好的学习方式是拆解大师的作品"

**Summary**: 本章是全书的高潮——深度解剖 5 个真实世界的优秀 Skill，从结构到细节，分析每一个设计决策背后的原因。这不是代码审查，而是"逆向工程一个好的思考过程"。

**Sections**:

- **11.1 解剖方法论** (~600 words)
  - 解剖 Skill 的 7 个维度清单
  - 如何从 Skill 的结构反推设计者的思考过程

- **11.2 案例 1：tech-book-writer（500 行，专业级 Skill）** (~2000 words)
  - 整体架构分析：14 个命令 + 6 个辅助文档 + 3 个脚本
  - description 分析：为什么这样写
  - 渐进式方法论如何融入 Skill 指令
  - 多步工作流的精妙设计（5-Pass 写作策略）
  - 质量检查清单的设计
  - 三层架构遵循"脚本优先原则"：确定性逻辑全部提取为脚本
  - 可借鉴的模式总结

- **11.3 案例 2：wechat-article-writer（内容创作 Skill）** (~1500 words)
  - 输入适配设计：URL + 粘贴文本双通道
  - 5-Pass 工作流的决策逻辑
  - 视觉风格系统：3 种风格 × 不同工具
  - 输出目录结构的设计
  - 约束条件的精确性（"30 字标题"、"60 字预览"）

- **11.4 案例 3：douyin-video-creator（跨媒介 Skill）** (~1500 words)
  - "3 秒法则"——如何在 Skill 中编码领域专家知识
  - 多输出格式：脚本 + 幻灯片 + 口播文本 + 视觉指导
  - 系列规划模式：从单次执行到系列策划
  - Hook 模板库——预设示例的威力

- **11.5 案例 4：obra/superpowers 合集（社区典范）** (~1200 words)
  - 20+ Skill 的统一设计语言
  - `/brainstorm` 和 `/execute-plan` 的元模式
  - 如何设计一个 Skill 家族而不是零散的 Skill
  - 社区贡献和维护模式

- **11.6 案例 5：Trail of Bits Security Skills（专业领域）** (~1200 words)
  - 安全分析领域的高精度要求
  - CodeQL / Semgrep 集成
  - 脚本密集型 Skill 的设计
  - 高脆弱度任务如何最大化确定性
  - 验证 EvoSkills 的洞察：确定性逻辑应分离为独立脚本而非自然语言指令

- **11.7 横向对比与模式总结** (~1200 words)
  - 5 个案例的共同模式
  - 不同领域 Skill 的设计差异
  - 你应该从每个案例中学到的一件事
  - **OpenClaw TOP 20 中三个互补案例**：
    - `deslop`（30 行极简主义范例）——证明好 Skill 不必长
    - `emergency-rescue`（模式复用范例）——单一 Diagnose-Fix-Verify 跨 20+ 场景
    - `checkmate`（安全模型前置范例）——Worker/Judge 分离架构

- **11.8 Try It Yourself** (~400 words)
  - Verify: 从 skill-of-skills 目录下载一个 Skill，用本章的方法论解剖它
  - Extend: 选一个你觉得不够好的社区 Skill，重写改进它
  - Explore: 用解剖方法论分析你自己写的 Skill，找出 3 个改进点

**Estimated word count**: ~9,900

---

### Chapter 12: 元技能：创建 Skill 的 Skill

> **Motto**: "教会 Agent 创建 Skill，你就不再是一个人在写"

**Summary**: 全书的终章——把前 11 章学到的所有知识编码成一个 Skill，让 Agent 自己帮你创建 Skill。这就是 Meta-Skill：一个遵循本书方法论的 `skill-creator` Skill。

**Sections**:

- **12.1 元编程思维** (~600 words)
  - 从"我写 Skill"到"Skill 帮我写 Skill"
  - 元技能的适用场景和限制

- **12.2 skill-creator 的设计** (~2100 words)
  - 需求收集：通过交互式问答确定 Skill 的用途
  - 结构生成：自动创建目录、SKILL.md、辅助文件
  - 质量验证：生成后自检是否符合最佳实践
  - 迭代优化：根据测试结果自动改进
  - **Anthropic 10 步创建-测试-迭代循环**：
    1. 捕获意图 → 2. 交互式访谈 → 3. 生成 SKILL.md → 4. 创建测试用例 → 5. 并行运行（with-skill + baseline）→ 6. 断言评估 → 7. 评分/聚合/可视化 → 8. 用户反馈 → 9. 迭代改进 → 10. Description 优化
  - 关键洞察：步骤 5 的"并行对比"是科学方法的核心——有对照组才有因果推断
  - 来源：Anthropic Skill-Creator Research（完整工作流）
  - **12.2.1 专门化子 Agent**
    - **Grader Agent**：评分子 Agent，给每个测试用例的输出独立打分（1-5 + 理由）
    - **Comparator Agent**：盲比较子 Agent，只看两份匿名输出做偏好选择，不知道哪份用了 Skill
    - **Analyzer Agent**：模式分析子 Agent，跨所有测试结果找共性模式和系统性缺陷
    - 设计哲学：每个子 Agent **单一职责 + 信息约束**，避免确认偏误
    - 来源：Anthropic Skill-Creator `agents/` 目录

- **12.3 实战：完整的 skill-creator SKILL.md** (~2000 words)
  - 逐段讲解 skill-creator 的每一部分
  - 如何将前 11 章的方法论编码为指令
  - description 写作规则 → 作为 skill-creator 的一个 Pass
  - 质量检查清单 → 作为 skill-creator 的最终验证

- **12.4 创建 Skill 的三条路径** (~800 words)
  - **路径 1：意图驱动**（Anthropic 风格）— 用户有想法 → skill-creator 辅助构建（本书主方法论）
    - 适用：明确知道想要什么 Skill
    - 流程：意图 → 访谈 → 生成 → 测试 → 迭代
  - **路径 2：失败驱动发现**（EvoSkill 风格）— 从 Agent 失败中提炼
    - "失败日志"：记录 Agent 做错的场景
    - 聚类相似失败 → 每个聚类是候选 Skill
    - 适用：有大量使用数据，想补齐 Agent 短板
    - EvoSkill 结果：42% → 51.3%（两轮进化）
    - 来源：EvoSkill (arxiv.org/abs/2603.02766)
  - **路径 3：领域数据初始化**（SkillForge 风格）— 从企业历史数据出发
    - 从工单/文档/运维手册提取工作流
    - 自动生成 Skill 草稿，人工精修
    - 适用：有丰富的企业知识库，想批量生产 Skill
    - SkillForge 结果：超越人工生产系统 13+ 百分点
    - 来源：SkillForge (arxiv.org/html/2604.08618v1)
  - 选择指南：有失败数据 → 路径 2，有企业文档 → 路径 3，全新想法 → 路径 1

- **12.5 用 skill-creator 创建一个 Skill** (~1000 words)
  - 实际演示：让 skill-creator 创建一个 `changelog-writer` Skill
  - 观察 Agent 如何应用本书的方法论
  - 对输出的质量评估

- **12.6 社区与分发** (~800 words)
  - Skill 的分发方式：Git repo、marketplace、团队共享
  - 版本管理和语义化版本号
  - 安全注意事项：审查第三方 Skill
  - Skill 生态的未来

- **12.7 回顾：你的 Skill 工程方法论** (~900 words)
  - 12 章的核心要点浓缩
  - Skill 工程的设计哲学
  - 从 Skill 作者到 Skill 架构师
  - **Skill 获取方法论全景图**（来自学术综述 arxiv.org/abs/2602.12430）：
    - 本书教授的方法：Manual Packaging + Structured Engineering
    - 前沿方向：强化学习自动发现 Skill、多 Agent 自主进化、动态 Skill 组合与压缩
    - 展望：从"人工写 Skill"到"Agent 自己发现 + 人类精修"的协作模式

- **12.8 Try It Yourself** (~400 words)
  - Verify: 用 skill-creator 创建一个你一直想要的 Skill
  - Extend: 改进 skill-creator 本身——这是一个递归！
  - Explore: 设计一个 Skill 测试框架，自动评估 Skill 质量

**Estimated word count**: ~8,600

---

## Total Estimated Word Count

| Phase | Chapters | Words |
|-------|----------|-------|
| Phase 1: First Skill | Ch 1-3 | ~16,400 |
| Phase 2: Core Craft | Ch 4-6 | ~18,500 |
| Phase 3: Architecture | Ch 7-9 | ~20,400 |
| Phase 4: Mastery | Ch 10-12 | ~26,800 |
| **Total** | **12 chapters** | **~82,100** |

加上前言、附录、术语表，预估总字数 **~90,000 - 100,000 中文字**。
    - 本书教授的方法：Manual Packaging + Structured Engineering
    - 前沿方向：强化学习自动发现 Skill、多 Agent 自主进化、动态 Skill 组合与压缩
    - 展望：从"人工写 Skill"到"Agent 自己发现 + 人类精修"的协作模式

- **12.8 Try It Yourself** (~400 words)
  - Verify: 用 skill-creator 创建一个你一直想要的 Skill
  - Extend: 改进 skill-creator 本身——这是一个递归！
  - Explore: 设计一个 Skill 测试框架，自动评估 Skill 质量

**Estimated word count**: ~8,600

---

## Total Estimated Word Count

| Phase | Chapters | Words |
|-------|----------|-------|
| Phase 1: First Skill | Ch 1-3 | ~19,000 |
| Phase 2: Core Craft | Ch 4-6 | ~21,200 |
| Phase 3: Architecture | Ch 7-9 | ~21,600 |
| Phase 4: Mastery | Ch 10-12 | ~31,000 |
| **Total** | **12 chapters** | **~92,800** |

加上前言、3 个附录、术语表，预估总字数 **~105,000 - 115,000 中文字**。

---

## Appendices

### 附录 A: Skill 十大反模式速查

10 个常见反模式：信息过载、重造轮子、触发模糊、无 Guardrails、过度内联代码、无验证环节、瑞士军刀、硬编码、无示例锚定、忽略边界条件。每个含问题/危害/修正 + 自检清单。

### 附录 B: Skill 上线前检查清单

23 项检查（5 类：核心质量 6 项、结构完整性 4 项、安全 5 项、代码脚本 4 项、测试 4 项）+ 5 分钟快速检查版。

### 附录 C: 全球 Skill 生态资源地图

8 大仓库索引、4 家官方 Skill 集合（Anthropic 16 个 / OpenAI 18 个 / Google 4 个 / HuggingFace 4 个）、9 平台兼容矩阵、发现工具、学术研究索引、本书案例来源索引。
