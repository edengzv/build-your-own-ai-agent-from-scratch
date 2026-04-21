# OpenClaw Skills 生态调研报告：TOP 20 Skills 与最佳实践

> 调研时间：2026-04-19
> 数据来源：github.com/openclaw/skills, github.com/VoltAgent/awesome-openclaw-skills, ClawHub Registry, 社区文章

---

## 一、OpenClaw Skills 生态概览

### 1.1 生态规模

OpenClaw 是一个开源的 AI Agent 平台，其 Skill 生态已发展到 **5,400+** 个技能，覆盖 30 个分类：

| 分类 | 技能数量 | 典型场景 |
|------|---------|---------|
| Coding Agents & IDEs | 1,200 | 代码代理、IDE集成、多Agent协作 |
| Web & Frontend Development | 924 | 前端开发、UI设计、全栈构建 |
| DevOps & Cloud | 392 | 部署、监控、云平台管理 |
| Search & Research | 352 | 学术研究、网络搜索、信息分析 |
| Browser & Automation | 322 | 浏览器自动化、RPA、数据抓取 |
| Productivity & Tasks | 205 | 任务管理、日程规划、自动化工作流 |
| Git & GitHub | 159 | 版本控制、PR管理、代码审查 |
| Clawdbot Tools | 37 | 平台核心工具、安全扫描、配置管理 |
| 其他22个分类 | ~1,800+ | AI/LLM、文档、安全、智能家居等 |

### 1.2 核心仓库

| 仓库 | 说明 |
|------|------|
| [openclaw/skills](https://github.com/openclaw/skills) | 官方技能归档仓库，所有 ClawHub 上的技能版本备份 |
| [openclaw/clawhub](https://github.com/openclaw/clawhub) | 公共技能注册中心，支持发布、版本管理、向量搜索 |
| [VoltAgent/awesome-openclaw-skills](https://github.com/VoltAgent/awesome-openclaw-skills) | 社区精选技能索引，按30个分类整理 |

### 1.3 Skill 文件结构

每个 Skill 的核心是一个 `SKILL.md` 文件，遵循渐进式加载架构：

```
my-skill/
├── SKILL.md              # 核心文件：YAML 元数据 + 指令正文
├── _meta.json            # ClawHub 元信息
├── references/           # 按需加载的详细文档（API规范、指南等）
├── scripts/              # 可执行脚本（Python、Bash），不加载到上下文
└── assets/               # 模板、Schema、图片等静态资源
```

---

## 二、TOP 20 优秀 Skills 精选

基于功能完整性、设计质量、社区影响力、SKILL.md 结构规范性四个维度评选：

### 2.1 开发工具类

#### 1. conventional-commits
- **作者**: bastos | **分类**: Git & GitHub
- **功能**: 按 Conventional Commits 规范格式化提交消息，支持语义化版本、变更日志自动生成
- **亮点**: 结构清晰的参考手册式设计，覆盖所有提交类型、作用域、Breaking Change 语法，提供正反示例对照
- **最佳实践体现**: 极简主义、示例驱动、完整的"何时使用"/"常见错误"指引

#### 2. deslop
- **作者**: brennerspear | **分类**: Coding Agents
- **功能**: 从分支 diff 中检测并移除 AI 生成的"slop"代码（冗余注释、空 catch、无意义防御性代码）
- **亮点**: 紧凑的工作流设计（6步），明确的 Guardrails（不移除信任边界保护），引用外部 references 文件
- **最佳实践体现**: 渐进式加载、明确护栏、行为保持原则

#### 3. anti-pattern-czar
- **作者**: glucksberg | **分类**: Coding Agents
- **功能**: 检测并修复 TypeScript 错误处理反模式，支持5种模式（scan/review/auto/resume/report）
- **亮点**: 状态持久化设计、审批工作流、严格的 override 条件（4项必须全满足）、进度输出格式
- **最佳实践体现**: 多模式分支、状态文件设计、references 分层、守卫条件

#### 4. emergency-rescue
- **作者**: gitgoodordietrying | **分类**: DevOps
- **功能**: 开发者灾难恢复工具包，覆盖 Git 灾难、凭证泄露、磁盘满、进程失控、数据库故障、部署回滚、SSH锁定等
- **亮点**: 每个场景遵循"诊断→修复→验证"三步模式，命令默认非破坏性，破坏性步骤明确标记
- **最佳实践体现**: 清单式推进、统一的问题处理模式、分场景决策树、实战Tips

#### 5. api-dev
- **作者**: gitgoodordietrying | **分类**: Web Development
- **功能**: API 全生命周期工具：脚手架、测试、文档生成、Mock 服务、调试
- **亮点**: 提供完整可运行的代码（Bash/Python 测试脚本、Mock 服务器、Express 脚手架），覆盖 CORS、JWT、性能测试
- **最佳实践体现**: 模板控制、多语言支持、实用 Tips 汇总

### 2.2 工作流与自动化类

#### 6. checkmate
- **作者**: insipidpoint | **分类**: Productivity
- **功能**: 确定性任务完成循环：将目标转化为通过/失败标准，运行 worker，评判输出，反馈缺失，循环直到所有标准通过
- **亮点**: 完整的安全与权限模型文档、Worker/Judge 架构图、交互式检查点、批量模式风险提示
- **最佳实践体现**: 安全模型前置声明、架构图ASCII化、用户控制点设计

#### 7. client-flow
- **作者**: ariktulcha | **分类**: Productivity
- **功能**: 一条消息完成客户入职全流程：创建项目文件夹、生成项目简报、发送欢迎邮件、安排启动会议、创建任务板、配置提醒
- **亮点**: 7步完整工作流、多工具适配（Google Drive/Dropbox/Notion/Todoist/ClickUp）、边界情况处理、模板可定制
- **最佳实践体现**: 端到端工作流设计、工具适配策略、Edge Cases 考虑

#### 8. agent-self-reflection
- **作者**: brennerspear | **分类**: Productivity
- **功能**: 定期自省近期会话，提取可操作洞察，路由到正确的工作区文件
- **亮点**: 明确的质量门槛（Specific/Actionable/Non-obvious/New）、文件路由规则、反模式清单
- **最佳实践体现**: 质量检查清单、Anti-Patterns 列表、分步骤执行

#### 9. adaptive-reasoning
- **作者**: enzoricciulli | **分类**: AI & LLMs
- **功能**: 自动评估任务复杂度并调整推理级别，作为响应前的预处理步骤
- **亮点**: 量化评分表（0-10维度打分）、决策阈值矩阵、自动降级机制、视觉指示器
- **最佳实践体现**: 结构化决策框架、无需外部工具、自适应机制

#### 10. commit-analyzer
- **作者**: bobrenze-bot | **分类**: Git & GitHub
- **功能**: 分析 git 提交模式以监控自治操作健康状况
- **亮点**: 健康指标表（Healthy/Warning/Critical阈值）、多种命令模式、集成方式说明、示例输出
- **最佳实践体现**: 指标驱动、可观测性设计、实际输出示例

### 2.3 设计与创作类

#### 11. awwwards-design
- **作者**: mkhaytman87 | **分类**: Web & Frontend
- **功能**: 创建获奖级别网站，包含高级动画、创意交互和独特视觉体验
- **亮点**: 设计哲学阐述、Awwwards 评分标准解读、核心动画技术栈推荐、完整代码模式
- **最佳实践体现**: 理论+实践结合、技术栈推荐、可运行代码示例

#### 12. anti-slop-design
- **作者**: kjaylee | **分类**: Web & Frontend
- **功能**: 创建独特的、生产级前端界面，避免通用 AI 美学
- **亮点**: 反向定义（什么不该做）+ 正向指引，关注 AI 生成代码的常见审美问题

### 2.4 安全与治理类

#### 13. agent-guardrails
- **作者**: olmmlo-cmd | **分类**: Security
- **功能**: 阻止 AI Agent 秘密绕过规则
- **亮点**: 安全防护视角的 Skill 设计，关注 Agent 行为边界

#### 14. agent-safety
- **作者**: compass-soul | **分类**: Security
- **功能**: 自主 AI Agent 的出站安全检查——在输出离开机器前扫描
- **亮点**: 防御性安全设计，关注数据泄露防护

#### 15. agent-audit-trail
- **作者**: roosch269 | **分类**: Security
- **功能**: 防篡改、哈希链式 AI Agent 审计日志
- **亮点**: 不可变审计链设计，适用于合规场景

### 2.5 研究与知识管理类

#### 16. academic-research
- **作者**: rogersuperbuilderalpha | **分类**: Search & Research
- **功能**: 使用 OpenAlex API 搜索学术论文并进行文献综述（免费，无需API Key）
- **亮点**: 零配置即用、聚焦单一数据源做深做透

#### 17. autonomous-research
- **作者**: tobisamaa | **分类**: Search & Research
- **功能**: 自主进行全面研究，无需持续人工干预
- **亮点**: 自治研究循环设计

#### 18. agent-brain
- **作者**: dobrinalexandru | **分类**: Search & Research
- **功能**: 本地优先的 AI Agent 持久记忆系统，SQLite 存储，混合检索
- **亮点**: 本地存储优先、结构化记忆分层

### 2.6 DevOps 与部署类

#### 19. agentic-devops
- **作者**: tkuehnl | **分类**: DevOps
- **功能**: 生产级 Agent DevOps 工具包——Docker、进程管理、日志分析、健康监控
- **亮点**: 完整的 DevOps 工具链集成

#### 20. agentscale
- **作者**: jpbonch | **分类**: Web & Frontend
- **功能**: 一条命令将 Web 应用和 API 部署到公共 URL
- **亮点**: 极简交互设计，单命令部署

---

## 三、SKILL.md 最佳实践 (Best Practices)

从 TOP 20 Skills 和官方文档中抽象出以下最佳实践体系：

### 3.1 元数据设计 (Metadata)

#### 规范
```yaml
---
name: my-skill-name          # kebab-case，仅小写字母+数字+连字符，最多64字符
description: >                # 1-2句话，第三人称，明确功能边界和触发场景
  Detect and fix TypeScript error handling anti-patterns with state
  persistence and approval workflows. Use when scanning a codebase for
  silent error failures, empty catches, or promise swallowing.
---
```

#### 最佳实践
- **name**: 使用动名词结构（如 `processing-pdfs`），避免 `utils`/`helper` 等模糊命名
- **description**: 必须采用第三人称，包含关键词以支持搜索，明确"做什么"和"何时用"
- **触发词嵌入**: 在 description 中嵌入用户可能说的触发短语（如 "Use when asked to..."）
- **反面示例**: 避免第一人称("I will...")、过于宽泛("A useful tool for many things")

### 3.2 极简至上 (Minimalism First)

#### 原则
上下文窗口是共享资源。Skill 应只补充模型未知的信息，避免冗余说明。

#### 最佳实践
- **主文件 < 500行**: 超出部分拆分到 `references/` 目录
- **简洁版 ~50 tokens**: 核心提示词控制在极小规模
- **不重复模型已知知识**: 不需要教 Agent 什么是 Git，只需告诉它你的特定约定
- **每个词都要有存在的理由**: 删掉任何"nice to have"的内容

**优秀案例 — `deslop`**: 整个 SKILL.md 仅 ~30 行，6步工作流 + 护栏 + 一个 references 链接

**反面案例 — `api-dev`**: 虽然内容全面，但主文件过长；更好的做法是将代码示例移入 references/

### 3.3 渐进式加载架构 (Progressive Loading)

#### 三层架构
```
Layer 1 - Metadata (总是加载): name + description
Layer 2 - Body (相关时加载): 核心指令
Layer 3 - Resources (按需加载): references/, scripts/, assets/
```

#### 最佳实践
- **主文件充当目录**: 指引模型按需读取子文件
- **引用深度 = 1**: 所有参考文件从主文件直接链接，避免多层嵌套
- **超100行的 references 顶部附目录**: 便于模型快速定位
- **单个 reference 文件 < 10,000 词**
- **脚本放 scripts/ 不放上下文**: 确定性操作封装为可执行脚本

**优秀案例 — `anti-pattern-czar`**:
```
SKILL.md (主文件 ~80行，概览+模式选择表)
├── references/workflows.md (各模式的详细工作流)
└── references/patterns.md (完整模式列表+代码模板)
```

**优秀案例 — `deslop`**:
```
SKILL.md (主文件 ~30行)
└── references/slop-heuristics.md (启发式规则详情)
```

### 3.4 自由度匹配 (Freedom Calibration)

#### 原则
根据任务稳定性设定指令强度：

| 任务类型 | 自由度 | 指令风格 |
|---------|--------|---------|
| 窄桥型（数据库迁移、安全操作） | 低 | 精确命令序列，每步验证 |
| 开阔地（代码审查、设计） | 高 | 方向性指引，允许自适应 |

#### 最佳实践
- **严格场景**: 提供固定结构模板，步骤不可跳过（如 `emergency-rescue` 的"诊断→修复→验证"）
- **灵活场景**: 提供基础框架+决策树，允许 Agent 根据上下文调整（如 `adaptive-reasoning` 的评分矩阵）
- **永远明确不可做的事**: Guardrails 比指令更重要

### 3.5 工作流设计模式 (Workflow Patterns)

#### Pattern 1: 清单式推进 (Checklist Progression)
```
Step 1: 执行任务A
Step 2: 执行任务B
...
Step N: 验证结果
```
**案例**: `client-flow`（7步入职流程）, `agent-self-reflection`（6步反思流程）

#### Pattern 2: 诊断→修复→验证 (Diagnose → Fix → Verify)
```
DIAGNOSE: 确认问题状态
FIX: 执行修复操作
VERIFY: 确认修复成功
```
**案例**: `emergency-rescue`（所有场景统一此模式）

#### Pattern 3: 循环反馈 (Iterative Feedback Loop)
```
执行 → 评判 → 反馈 → 重试（直到通过）
```
**案例**: `checkmate`（Worker/Judge 循环）, `anti-pattern-czar`（scan → fix → report）

#### Pattern 4: 条件分支 (Decision Tree)
```
IF 用户意图 == A → 执行流程 A
IF 用户意图 == B → 执行流程 B
```
**案例**: `anti-pattern-czar`（5种模式的意图解析表）

#### Pattern 5: 量化决策 (Quantified Decision)
```
Score = 维度1(权重) + 维度2(权重) - 减分项
IF Score >= 阈值 → 行动A ELSE → 行动B
```
**案例**: `adaptive-reasoning`（0-10维度打分 + 阈值决策）

### 3.6 示例驱动 (Example-Driven)

#### 最佳实践
- **输入/输出对照**: 提供期望的输入输出对，比纯文字描述更直观
- **正反示例对比**: 同时展示"应该"和"不应该"（如 `conventional-commits` 的 Common Mistakes）
- **真实输出示例**: 展示 Skill 实际运行的输出格式（如 `commit-analyzer` 的 CLI 输出示例）
- **代码可运行**: 提供的代码应能直接复制运行（如 `api-dev` 的测试脚本）

**优秀案例 — `conventional-commits`**:
```
❌ `Added new feature` (past tense, capitalized)
✅ `feat: add new feature` (imperative, lowercase)

❌ `fix: bug` (too vague)
✅ `fix: resolve null pointer exception in user service`
```

### 3.7 护栏与安全 (Guardrails & Safety)

#### 最佳实践
- **明确列出"不可做"**: 比指令更重要的是限制（如 `deslop` 的 Guardrails 部分）
- **安全模型前置**: 高权限 Skill 必须在开头声明安全模型（如 `checkmate` 的 Security & Privilege Model）
- **破坏性操作标记**: 标记 ⚠️ 并要求确认（如 `emergency-rescue` 的 "⚠️ destructive"）
- **Anti-Patterns 清单**: 明确列出不该做的事（如 `agent-self-reflection` 的 5 个 ❌ 反模式）
- **默认安全**: 命令默认非破坏性，破坏性选项需显式启用

### 3.8 闭环验证 (Closed-Loop Verification)

#### 最佳实践
- **执行→校验→修正→重试**: 关键操作引入验证步骤（如 `anti-pattern-czar` 的 SCAN → FIX → VERIFY）
- **中间产物校验**: 高风险操作先生成计划文件，验证后再执行
- **质量检查清单**: 完成前逐项检查（如 `agent-self-reflection` 的 Quality Checklist）
- **每次恢复操作以验证结束**: "Don't assume — confirm"

### 3.9 指令语言规范 (Instruction Language)

#### 最佳实践
- **使用祈使句**: "Load the config" 而非 "You should load the config"
- **避免第二人称**: 不用 "If you need to..."
- **表格优于段落**: 用 Markdown 表格呈现结构化信息（如模式选择、评分矩阵、健康指标）
- **ASCII 架构图**: 用文字绘制架构图（如 `checkmate` 的 Architecture 部分）
- **统一使用正斜杠**: 路径一律 `/`，确保跨平台兼容

### 3.10 多模型兼容 (Multi-Model Compatibility)

#### 最佳实践
- **分别测试**: 在轻量型、均衡型、强推理型模型上验证
- **避免模型特定特性**: 不依赖特定模型的 system prompt 能力
- **提示词普适性**: 确保指令对各模型均有效
- **降级策略**: 某工具不可用时提供替代方案（如 `client-flow` 的多工具适配）

---

## 四、Skill 设计反模式 (Anti-Patterns to Avoid)

| 反模式 | 说明 | 修正方向 |
|--------|------|---------|
| **信息轰炸** | 主文件几千行，一次性加载全部内容 | 拆分到 references/，渐进式加载 |
| **重复造轮子** | 教模型已知知识（如 Git 基础） | 只补充特定约定和上下文 |
| **模糊触发** | description 过于宽泛，无法精准匹配 | 嵌入具体触发词和场景 |
| **无护栏** | 没有任何限制和安全边界 | 添加 Guardrails/Anti-Patterns 部分 |
| **代码内联过多** | 大量代码示例堆在主文件中 | 代码移入 scripts/ 或 references/ |
| **缺乏验证** | 执行后不检查结果 | 添加 VERIFY 步骤 |
| **万能 Skill** | 试图做所有事情 | 聚焦单一职责，做深做透 |
| **硬编码** | 路径、时间、API Key 写死 | 使用环境变量和相对路径 |
| **无示例** | 纯理论描述，没有输入输出示例 | 添加正反示例和实际输出 |
| **忽略边界情况** | 只考虑正常路径 | 添加 Edge Cases 部分 |

---

## 五、Skill 发布检查清单 (Pre-Launch Checklist)

### 核心质量
- [ ] name 使用 kebab-case，64字符以内
- [ ] description 精准，包含关键词和触发场景
- [ ] 主文件 < 500 行，低于 5,000 词
- [ ] 术语统一，无自相矛盾
- [ ] 提供具体示例（输入/输出对照）
- [ ] 所有 references 文件从主文件直接链接（单层引用）

### 安全与护栏
- [ ] 明确列出"不可做"的事项
- [ ] 破坏性操作有 ⚠️ 标记
- [ ] 高权限操作有安全模型声明
- [ ] 无硬编码凭证或时效性信息

### 代码与脚本
- [ ] 代码示例可直接运行
- [ ] 异常处理完善，无隐藏常量
- [ ] 关键步骤包含验证命令
- [ ] 路径使用正斜杠，相对路径

### 测试覆盖
- [ ] 至少3组测试场景
- [ ] 覆盖不同模型（轻量/均衡/强推理）
- [ ] 包含边界情况测试
- [ ] 真实工作流验证（非仅语法检查）

---

## 六、从优秀 Skills 中提炼的设计哲学

### 哲学 1: Less is More
> 最好的 Skill 不是内容最多的，而是每个词都不可删除的。
> —— `deslop`（30行）比 `api-dev`（500+行）在"效率/内容"比上更优

### 哲学 2: 模式复用
> 建立统一的问题处理模式，然后在不同场景中复用。
> —— `emergency-rescue` 的"诊断→修复→验证"贯穿全文20+场景

### 哲学 3: 防御性设计
> 告诉 Agent 不该做什么，比告诉它该做什么更重要。
> —— `checkmate` 的安全模型、`deslop` 的 Guardrails、`agent-self-reflection` 的 Anti-Patterns

### 哲学 4: 可观测性
> 如果不能度量，就不能改进。提供明确的输出格式和进度指示。
> —— `commit-analyzer` 的健康指标表、`anti-pattern-czar` 的进度条

### 哲学 5: 优雅降级
> 不是所有工具都可用。为每个依赖提供替代路径。
> —— `client-flow` 对 Google Drive/Dropbox/本地文件系统/Notion 的多路适配

---

## 七、参考资源

| 资源 | 链接 |
|------|------|
| OpenClaw 官方技能创建文档 | https://docs.openclaw.ai/tools/creating-skills |
| ClawHub 技能注册中心 | https://github.com/openclaw/clawhub |
| 全量技能归档 | https://github.com/openclaw/skills |
| Awesome Skills 精选索引 | https://github.com/VoltAgent/awesome-openclaw-skills |
| SKILL.md 格式指南 | https://lzw.me/docs/opencodedocs/numman-ali/openskills/advanced/skill-structure/ |
| Skills 最佳实践（中文） | https://www.cnblogs.com/elesos/p/19620343 |
