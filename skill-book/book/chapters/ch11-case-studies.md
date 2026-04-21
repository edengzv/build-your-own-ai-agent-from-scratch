# Chapter 11: 案例解剖室

> **Motto**: "最好的学习方式是拆解大师的作品"

> 你已经掌握了写 Skill 的全部技巧和评估方法。但理论不如实战——本章我们走进"解剖室"，用手术刀般的精度拆解 5 个真实世界的优秀 Skill。每个案例都会分析它的设计决策、优点、可改进之处，以及你能带走的模式。

![Chapter 11: 案例解剖室](images/ch11-case-studies.png)

## 11.1 解剖方法论

对每个 Skill，我们按 7 个维度分析：

1. **定位与 description**：精准度如何？覆盖面够吗？
2. **结构与组织**：文件架构、章节组织是否清晰？
3. **指令质量**：可执行性、精确度、自由度是否合适？
4. **工作流设计**：Multi-Pass 的 Pass 划分是否合理？
5. **锚定手段**：示例、模板、反例是否充分？
6. **质量控制**：Checklist 是否完善？
7. **工具编排**：工具使用是否合理？

每个案例最后会总结"你应该从这个案例中偷的一招"。

## 11.2 案例 1：tech-book-writer — 专业级 Skill 的典范

**规模**：SKILL.md 500 行 + 6 个辅助 .md + 4 个脚本 + 3 个模板

### 定位与 description

```yaml
description: Write O'Reilly-quality technical books on AI and related topics using progressive, step-by-step methodology. Handles book planning, chapter outlining, drafting, reviewing, and consistency checking. Use when the user wants to write a tech book, draft chapters, create book outlines, or review technical writing. Supports Markdown output with professional structure.
```

分析：
- **What**: "Write O'Reilly-quality technical books" — 清晰的动作和质量标准
- **When**: "when the user wants to write a tech book, draft chapters..." — 列出了多种触发场景
- **覆盖面**: 涵盖了 plan/outline/draft/review 等多个关键词
- **评分**: 9/10 — 唯一可改进的是加上中文触发词（因为用户可能用中文请求）

### 结构与组织

```
SKILL.md (500 行)
├── Commands (14 个命令表)
├── Book Directory Structure
├── Progressive Methodology (引用辅助文件)
├── Writing Style Rules
├── Multi-Pass Strategy
├── Review Checklist
└── Important Constraints

辅助文件:
├── progressive-methodology.md  ← 方法论深入
├── style-guide.md              ← 写作风格
├── illustration-guide.md       ← 插图系统
├── bilingual-guide.md          ← 翻译规则
├── pdf-pipeline.md             ← PDF 生成
└── templates/                  ← 模板集合
```

分析：
- **三层架构教科书级应用**：SKILL.md 保持在 500 行内，复杂知识全部外移
- **每个辅助文件单一主题**：不会让 Agent 在不需要翻译时加载翻译指南
- 14 个命令清晰地映射到写书的每个阶段

### 指令质量

亮点是 **Multi-Pass 写作策略**——5 步法：

```
Pass 1 — Skeleton: 只写标题和一句话描述
Pass 2 — Core Content: 写正文，标记代码占位符
Pass 3 — Code & Figures: 填充代码和图片
Pass 4 — Polish: 过渡、提示框、交叉引用
Pass 5 — Self-Review: 对照 checklist 自检
```

这个设计的精妙之处：它不只是"分步执行"，而是**每步的认知负担不同**——Pass 1 只需要结构思维，Pass 2 需要叙事能力，Pass 3 需要编码能力。分离不同认知模式，让每个 Pass 的输出质量都更高。

### 质量控制

Review Checklist 有 20+ 项，分为 4 大类：技术质量、渐进结构、写作风格、完整性。

特别值得学习的是**渐进结构**类：

```
- [ ] Chapter introduces exactly ONE new concept/capability
- [ ] Opens with a concrete problem the reader can feel
- [ ] Code builds on previous chapter's code (not from scratch)
- [ ] No forward references to unexplained concepts
```

这些不是通用的"写得好不好"，而是**针对本书方法论的特定检查**——每个检查项都对应一个可能犯的具体错误。

### 你应该偷的一招

**5-Pass 按认知模式分离**：如果你的 Skill 需要做不同类型的思考（结构 vs 内容 vs 格式），把它们分到不同的 Pass。不要让 Agent 同时做创意写作和格式检查。

## 11.3 案例 2：wechat-article-writer — 内容创作 Skill

**规模**：SKILL.md 175 行 + 4 个辅助 .md + 3 个模板

### 亮点 1：双通道输入设计

```markdown
## Input Methods

支持两种输入方式：
1. **URL 输入**：提供 1-3 个同一话题的英文文章 URL
2. **文本输入**：直接粘贴文章原文（适用于付费墙文章）

混合使用也可以：部分 URL + 部分粘贴文本。
```

这个设计考虑到了真实使用场景——很多高质量文章在付费墙后面，无法通过 URL 抓取。提供第二种输入方式让 Skill 的适用范围翻倍。

### 亮点 2：精确的平台约束

```markdown
- 标题：30 个中文字符以内，引人注目，不标题党
- 开头 60 字：必须能独立成段，作为微信信息流预览文案
- 正文：2000-4000 中文字符
- 代码块：不超过 15 行
```

这些数字不是随便定的——它们来自微信公众号的平台规则和阅读体验最佳实践。把平台约束编码为 Skill 的约束条件，是领域 Skill 的关键设计模式。

### 亮点 3："不是翻译"的定位

```markdown
## Important Constraints
- **绝不能只是翻译**：必须加入原创分析、中国视角、实践建议
```

这一条约束比十页的写作指南都有效。它直接解决了 LLM 处理翻译型任务时最常犯的错误——直译。

### 你应该偷的一招

**把平台规则编码为约束**：如果你的 Skill 面向特定平台（微信、GitHub、Jira），把平台的格式规则、字数限制、不支持的功能都写成具体的约束条件。

## 11.4 案例 3：douyin-video-creator — 跨媒介 Skill

**规模**：SKILL.md 200 行 + 4 个辅助 .md + 5 个 HTML 模板

### 亮点 1：领域专家知识编码

```markdown
## The 3-Second Rule

抖音的前 3 秒决定用户是否划走。每个视频的前 3 秒必须做到以下之一：
- 抛出一个反直觉的事实
- 提出一个引发好奇的问题
- 展示一个惊人的对比
- 做出一个大胆的断言
```

这不是 LLM 内置知识——这是**短视频创作者的行业经验**。把这种隐性知识编码成 Skill 指令，是 Skill 最大的价值所在。

### 亮点 2：多输出格式

```
输出：
├── brief.md          → 内容摘要
├── script.md         → 三栏脚本（时间|口播|画面）
├── voiceover.txt     → 纯净口播（给 TTS 用）
├── visual-direction.md → 剪辑指导
└── slides/           → 竖屏幻灯片 HTML
```

一个 Skill 输出 5 种不同格式的文件——每种面向不同的下游使用者（演讲者、剪辑师、TTS 引擎、设计师）。这是**面向工作流的输出设计**。

### 亮点 3：脚本三栏格式

```
| 时间       | 口播文本                    | 画面指导              |
|-----------|---------------------------|---------------------|
| 0:00-0:03 | **90%的开发者**不知道这个技巧 | 标题卡，文字弹入特效    |
```

表格格式让脚本同时承载时间轴、台词和画面指导——所有视频制作需要的信息都在一个视图里。

### 你应该偷的一招

**编码领域专家知识**：问自己"一个这个领域的专家知道、但 LLM 不一定知道的经验法则是什么？"把这些法则写进 Skill。

## 11.5 案例 4：lovstudio/any2deck — 选项爆炸的驯服术

**规模**：SKILL.md 300+ 行，16 种视觉风格，references/ 目录

**来源**：lovstudio/skills 生态——一个拥有 33 个 Skill 的商业级生态系统 (https://github.com/lovstudio/skills)

### 定位与 description

```yaml
name: any2deck
description: |
  将任何内容转换为精美的演示幻灯片。
  Convert any content into beautifully designed presentation slides.
  - 支持 Markdown、文章链接、主题描述等多种输入
  - 16种视觉风格可选
  当用户想要创建幻灯片、PPT、演示文稿、presentation时使用
```

分析：
- **双语触发**：中文 + 英文描述，覆盖两种语言用户
- **输入多样性**：明确列出了支持的输入类型
- **关键词覆盖**：幻灯片、PPT、演示文稿、presentation——四个同义词
- **评分**: 9/10

### 亮点 1：扩展 YAML Frontmatter

```yaml
---
name: any2deck
description: ...
category: 生产力
tagline: "让每一页都能讲故事"
license: MIT
compatibility: claude-code, qoder
metadata:
  author: lovstudio
  version: 2.1.0
  tags: [slides, presentation, deck, ppt]
---
```

这比标准的 `name + description` 丰富得多：
- `category` + `tags`：支持 Skill 市场的分类和搜索
- `tagline`：一句话卖点，面向人类而非 Agent
- `version`：语义化版本号，支持生态管理
- `compatibility`：声明兼容的 Agent 平台

**启示**：如果你的 Skill 要在生态中分发，扩展 Frontmatter 是零成本的元数据投资。

### 亮点 2：AskUserQuestion 强制交互

```markdown
## MANDATORY: 开始前必须确认

在执行任何操作之前，**必须**使用 AskUserQuestion 工具确认：
1. 输入内容是什么？（URL/文本/主题）
2. 目标风格？（展示 16 种风格的选项列表）
3. 幻灯片数量偏好？
4. 是否有品牌色/Logo？

**绝不跳过确认步骤。** 即使用户在初始消息中提供了部分信息。
```

这个设计值得深思——为什么要**强制**交互，即使用户已经说了一些信息？

原因：any2deck 有 16 种风格 × N 种输入 × 多种数量选项，组合空间爆炸。如果让 Agent 自己猜用户想要什么风格，猜错了就浪费整个生成过程。**在选项空间巨大时，花 30 秒确认比花 5 分钟重做更经济**。

### 亮点 3：Checklist 驱动的进度追踪

```markdown
## 工作流追踪

每完成一个阶段，在输出中标记进度：

```
进度检查：
- [x] 用户需求已确认
- [x] 内容大纲已提取
- [ ] 幻灯片结构已设计
- [ ] 视觉风格已应用
- [ ] 最终输出已生成
```
```

这不是质量 Checklist（Ch9），而是**进度 Checklist**——让用户实时看到 Agent 走到了哪一步。对于长时间运行的 Skill（生成 20 页幻灯片可能要几分钟），进度可见性极大提升用户体验。

### 你应该偷的一招

**选项空间大时，强制 AskUserQuestion 交互**：如果你的 Skill 有超过 3 个重要的配置选项，不要让 Agent 猜——用 AskUserQuestion 明确询问。进度 Checklist 可以让用户在等待时保持信心。

## 11.6 案例 5：lovstudio/skill-optimizer — 自动化 Lint-Fix-Bump 管线

**规模**：SKILL.md 200+ 行，自动化审计管线

### 定位与 description

```yaml
name: skill-optimizer
description: |
  自动审计和优化 SKILL.md 文件质量。
  Automatically audit and optimize SKILL.md file quality.
  执行 lint检查→自动修复→版本升级→更新CHANGELOG 的完整管线。
  当用户想要检查skill质量、优化skill、升级skill版本时使用。
```

分析：
- **What**："审计和优化 SKILL.md"——极度精准
- **How**：直接在 description 中预告了管线流程（lint→fix→bump→changelog）
- **When**："检查质量、优化、升级版本"——三种触发场景

### 亮点 1：四阶段自动管线

```markdown
## 执行流程

### Stage 1 — Lint（审计）
对 SKILL.md 执行以下检查：
- [ ] YAML Frontmatter 格式正确
- [ ] description 长度 50-200 字
- [ ] 包含 category 和 version 字段
- [ ] Markdown 标题层级正确（h1 → h2 → h3，不跳级）
- [ ] 有 Quality Checklist 章节
- [ ] 代码块标注了语言类型

### Stage 2 — Fix（修复）
对 Stage 1 发现的问题自动修复：
- 缺失字段 → 补充默认值
- 格式错误 → 自动修正
- 缺少 Checklist → 根据 Skill 内容生成 5-8 项

### Stage 3 — Bump（版本升级）
根据修改范围决定版本号：
- 只修格式 → patch（1.0.0 → 1.0.1）
- 增加内容 → minor（1.0.0 → 1.1.0）
- 重写核心逻辑 → major（1.0.0 → 2.0.0）

### Stage 4 — Changelog
在 CHANGELOG.md 中记录本次变更。
```

这是本书见过的第一个**把 Skill 质量管理本身编码为 Skill** 的案例。它不是写新 Skill——而是**维护已有 Skill 的质量**。

### 亮点 2：语义化版本与跨仓同步

```markdown
## 版本同步

更新版本后，同步以下位置：
1. SKILL.md Frontmatter 中的 `metadata.version`
2. README.md 中的版本徽章
3. 根仓库 `skills.yaml` 索引中的版本号
4. CHANGELOG.md 中添加新条目
```

在 lovstudio 的 33-Skill 生态中，每个 Skill 是独立 Git 仓库，但通过一个中央 `skills.yaml` 索引文件管理。skill-optimizer 的版本同步确保了**生态的一致性**——单个 Skill 的变更能自动传播到全局索引。

### 亮点 3：Lint 规则即最佳实践编码

skill-optimizer 的 Lint 规则本质上是**把本书前 10 章的方法论编码为自动检查**：

| Lint 规则 | 对应本书章节 |
|-----------|------------|
| description 长度 50-200 字 | Ch2 三步法 |
| 标题层级不跳级 | Ch3 结构化指令 |
| 有 Quality Checklist | Ch9 质量自检 |
| 代码块标注语言 | Ch6 模板锚定 |
| 包含 version 字段 | Ch10 版本管理 |

**方法论如果不能自动检查，就容易被遗忘。** skill-optimizer 把"应该做到"变成了"自动检查是否做到"。

### 你应该偷的一招

**为你的 Skill 生态建立自动化质量管线**：如果你管理多个 Skill，写一个 skill-optimizer 类的 Skill 来自动审计它们。把最佳实践编码为 Lint 规则比写在文档里有效得多。

## 11.7 案例 6：lovstudio/any2pdf — "踩坑记录"设计模式

**规模**：SKILL.md 250+ 行，14 种主题，references/ 目录

### 亮点 1："Hard-Won Lessons"（血泪教训）章节

```markdown
## Hard-Won Lessons（踩坑记录）

以下问题是在实际使用中发现的，请严格遵守：

### CJK 渲染
- **问题**：WeasyPrint 默认字体不支持中文，输出为方块
- **解决**：必须在 CSS 中指定 `font-family: "Noto Sans CJK SC", sans-serif`
- **陷阱**：即使指定了字体，`font-weight: bold` 可能回退到默认字体

### 代码块溢出
- **问题**：长代码行超出页面宽度，被截断而非换行
- **解决**：CSS 中必须设置 `pre { white-space: pre-wrap; word-break: break-all; }`
- **陷阱**：`overflow-x: auto` 在 PDF 中无效（PDF 不支持滚动）

### 图片路径
- **问题**：Markdown 中的相对路径图片在 PDF 生成时找不到
- **解决**：生成前将所有图片路径转为绝对路径
- **陷阱**：URL 图片需要先下载到本地，远程图片在 PDF 渲染时可能超时
```

这个设计模式是**全新的**——我们在前 10 章从未讨论过。它不是指令、不是约束、不是 Checklist，而是**调试经验的编码**。

为什么这极其有效？因为 LLM 的训练数据中包含大量"正确做法"，但很少包含"看起来正确但实际会出错的陷阱"。`Hard-Won Lessons` 精准填补了这个知识缺口。

### 亮点 2：主题系统设计

```markdown
## 可用主题

| # | Theme | 适用场景 | 特点 |
|---|-------|---------|------|
| 1 | academic | 论文、学术报告 | 衬线字体，严谨排版 |
| 2 | corporate | 商务文档 | 品牌色，页眉页脚 |
| 3 | minimal | 技术文档 | 无装饰，专注内容 |
| ... | ... | ... | ... |
| 14 | dark | 技术演示 | 深色背景，代码友好 |

### 主题选择指引
- 不确定 → 默认 `minimal`
- 有品牌要求 → `corporate`，并询问品牌色
- 代码密集 → `dark` 或 `minimal`
```

注意**决策树式的选择指引**——不只列出选项，还告诉 Agent 在什么情况下选什么。这减少了 Agent 的"选择焦虑"，也减少了需要询问用户的次数。

### 亮点 3：Pre-fill from Context 模式

lovstudio 的另一个 Skill `fill-form`（表单填写）揭示了一个精妙的模式——**先从上下文预填，再让用户确认**：

```markdown
## 执行步骤

### Pass 1 — 智能预填
1. 读取用户提供的材料（简历、项目说明等）
2. 读取用户的 Memory（如有）
3. 尽可能填充表单字段
4. 对无法确定的字段标记 `[待确认]`

### Pass 2 — 用户确认
使用 AskUserQuestion 展示预填结果：
- 已填字段：展示填充值，允许修改
- 待确认字段：要求用户提供
```

这比"问一堆问题"好得多——用户只需要确认和补充，而不是从零填写。

### 你应该偷的一招

**在 Skill 中添加"Hard-Won Lessons"章节**：每当你在使用 Skill 的过程中踩坑——输出有微妙的错误、某个工具的行为和预期不同、某个格式在特定场景下失效——把它记录到 Skill 的 Hard-Won Lessons 中。这些经验是 Skill 最独特的价值，因为它们无法从通用训练数据中获得。

## 11.8 OpenClaw 社区极简设计典范

前面的案例都是 200+ 行的中大型 Skill。但 OpenClaw 社区证明了一个事实：**有些最有效的 Skill 只有 30 行**。

### deslop — 30 行的极简力量

`deslop` 是一个清理 AI 生成代码风格的 Skill。它的整个 SKILL.md 只有约 30 行：

```markdown
---
name: deslop
description: Remove AI-style code slop from a branch...
allowed-tools: [Bash]
---

## When to use this skill
Use when asked to: "remove AI slop", "clean up generated code style"...

## Workflow
1. Set comparison base and inspect `git diff <base>...HEAD`.
2. Build candidate list using `rg` over added lines.
3. Review each candidate in full file context.
4. Remove only inconsistent slop; keep behavior and domain-valid guards.
5. Re-run project checks and fix regressions.
6. Report exact files changed.

## Slop checklist
Read and apply: [references/slop-heuristics.md](references/slop-heuristics.md)

## Guardrails
- Do not remove protections at trust boundaries.
- Do not replace real typing with weaker typing.
- Prefer minimal edits over broad rewrites.
```

分析：
- **30 行主文件 + 1 个 references 文件**——完整的功能描述 + 安全护栏
- **每个句子都不可删除**——这是极简设计的标志
- **Guardrails 比指令还长**——体现了"告诉 Agent 什么不该做比告诉它该做什么更重要"的原则
- **references/ 按需加载**——具体的 slop 启发式规则在辅助文件中

### emergency-rescue — 模式复用的极致

`emergency-rescue` 用同一个三段式结构（DIAGNOSE → FIX → VERIFY）处理了 20+ 种 Git 灾难场景。我们在第 4 章用它展示了"诊断-修复-验证"模式，这里再看一个设计亮点：

```markdown
### Scenario: accidentally deleted a branch
# DIAGNOSE
git reflog | grep "branch-name"
# FIX
git checkout -b branch-name <commit-hash-from-reflog>
# VERIFY
git log --oneline -5 branch-name
```

每个场景都严格遵循同一模板。这种**模式复用**让 20+ 场景在一个 Skill 中共存，而 Agent 不会迷失——因为无论遇到哪种场景，处理流程都是一样的。

### 你应该偷的一招

**极简自检法**：写完 Skill 后，对每个句子问"删掉它，Agent 的行为会变差吗？"如果答案是"不会"，删掉。`deslop` 30 行 > `api-dev` 500+ 行——不是因为 deslop 的功能少，而是因为它每个词都在做功。

## 11.9 横向对比与模式总结

| 维度 | tech-book-writer | wechat-article | douyin-video | any2deck | skill-optimizer | any2pdf | deslop |
|------|-----------------|----------------|-------------|----------|----------------|---------|--------|
| 行数 | 500 | 175 | 200 | 300+ | 200+ | 250+ | 30 |
| Pass 数 | 5 | 5 | 5 | 4 | 4 (Stage) | 3 | 1 |
| 命令数 | 14 | 7 | 6 | 3 | 3 | 4 | 1 |
| Guardrails | 隐式 | 隐式 | 隐式 | 隐式 | 隐式 | Hard-Won | 显式 3 条 |
| 核心模式 | 认知分离 | 平台约束 | 领域专家知识 | 强制交互 | 自动化管线 | 踩坑记录 | 极简 + 护栏 |

**7 个案例，7 种不同的"最佳模式"**——这再次证明不存在"万能的 Skill 模板"。好的 Skill 设计是**根据领域特性做正确的 trade-off**。从 500 行到 30 行，每种规模都有做好的方式。

### lovstudio 生态的独特贡献

从 lovstudio 的 33-Skill 生态中，我们提炼出 3 个全新的设计模式：

1. **强制交互模式（AskUserQuestion Mandatory）**：选项空间大时，确认比猜测更经济
2. **自动化质量管线（Lint→Fix→Bump→Changelog）**：把最佳实践编码为自动检查
3. **踩坑记录（Hard-Won Lessons）**：LLM 训练数据中缺失的特定领域调试经验

这些模式在本书前 10 章中尚未涉及——它们来自**大规模 Skill 生产实践**，是单个 Skill 作者不太容易发现的。

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 只看过自己写的 Skill | 解剖了 6 个不同风格的专业 Skill |
| 设计凭直觉 | 有了多个可借鉴的模式 |
| 不知道不同领域的差异 | 理解了领域特性如何影响设计 |
| 没见过商业级 Skill 生态 | 理解了 lovstudio 33-Skill 生态的设计决策 |

## Try It Yourself

> 本章的实践工具见 `code/track-1/ch11-analysis/`，包含 7 维度分析模板和 deslop 案例报告。
>
> **Track 2 演进**：对比 `code/track-2/v10-eval/` 和 `code/track-2/v11-informed/` 的 diff，
> 观察 Pass 0 复杂度路由、7 维审查和案例注入如何从 437 行扩展到 506 行。

1. **Verify**: 从 lovstudio/skills (https://github.com/lovstudio/skills) 下载一个你感兴趣的 Skill，用本章的 7 维度方法论解剖它。写一份 500 字的解剖报告。
2. **Extend**: 给你现有的一个 Skill 添加"Hard-Won Lessons"章节——回忆它在使用中出过的问题，把解决方案编码进去。
3. **Explore**: 写一个 `skill-linter` Skill（参考 lovstudio 的 skill-optimizer），自动检查 SKILL.md 是否符合本书方法论。
4. **Challenge**: 选一个你觉得可以改进的社区 Skill，用 7 维度方法论重写并提交 PR。

## Summary

- **7 维度解剖法**：定位、结构、指令、工作流、锚定、质量控制、工具编排
- 7 个核心模式：认知分离（tech-book-writer）、平台约束（wechat-article）、领域专家知识（douyin-video）、强制交互（any2deck）、自动化管线（skill-optimizer）、踩坑记录（any2pdf）、**极简+护栏（deslop）**
- 好的 Skill 设计是根据**领域特性做正确的 trade-off**
- 每个案例都有"你应该偷的一招"——具体、可操作、可迁移
- **30 行可以比 500 行更有效**——极简自检法：删掉不会影响行为的句子
- lovstudio 生态带来 3 个全新模式：**强制交互、自动化质量管线、Hard-Won Lessons**
- OpenClaw 社区证明了**模式复用**的力量——同一模板处理 20+ 场景

## Further Reading

- lovstudio/skills (https://github.com/lovstudio/skills)：33 个商业级 Skill 的开源生态
- skill-of-skills 目录：686+ Skill 的开源合集
- awesome-claude-skills：精选社区 Skill 列表
- 第 12 章《元技能》——把解剖方法论编码成一个自动分析 Skill 质量的元 Skill
