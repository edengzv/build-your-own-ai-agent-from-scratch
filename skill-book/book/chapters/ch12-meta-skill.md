# Chapter 12: 元技能：创建 Skill 的 Skill

> **Motto**: "教会 Agent 创建 Skill，你就不再是一个人在写"

> 全书的终章。你已经掌握了 Skill 工程的完整方法论——从 description 到三层架构，从 Multi-Pass 到质量自检。现在，我们把这些知识编码成一个 Skill 本身：一个能帮你创建其他 Skill 的 Skill。这就是**元技能（Meta-Skill）**。

![Chapter 12: 元技能：创建 Skill 的 Skill](images/ch12-meta-skill.png)

## The Problem

你的同事看了你写的 Skill 工具箱，想为自己的工作流也写几个 Skill。但他没读过这本书——他不知道 description 的三步法，不知道五要素结构，不知道什么时候需要 Multi-Pass。

你可以把这本书推荐给他。但更好的方式是：**让 Agent 在创建 Skill 时自动应用这些方法论**。

## The Solution

`skill-creator` 是一个元 Skill——它的指令不是"做某个具体任务"，而是"创建一个做某个具体任务的 Skill"。它把前 11 章的方法论编码为 Agent 在创建 Skill 时必须遵循的流程。

## 12.1 skill-creator 的设计

```markdown
---
name: skill-creator
description: 交互式创建高质量的 Agent Skill。通过问答收集需求，生成符合最佳实践的 SKILL.md 文件。当用户想创建新 Skill、编写 SKILL.md 或设计 Agent 技能时使用。
---

# Skill Creator

通过交互式问答，帮助用户创建高质量的 Agent Skill。

## Commands

| Command | Purpose |
|---------|---------|
| `/skill-creator create` | 完整流程：需求收集 → 生成 → 验证 |
| `/skill-creator review <path>` | 审查已有 Skill 的质量 |
| `/skill-creator improve <path>` | 基于审查结果改进已有 Skill |

## `/skill-creator create`

### Pass 1 — 需求收集

通过 AskUserQuestion 收集以下信息：

**必须收集：**
1. 这个 Skill 做什么？（一句话描述）
2. 什么场景下使用？（触发条件）
3. 输入是什么？（用户会提供什么信息）
4. 输出是什么？（期望的产出是什么格式）
5. 有没有必须遵守的规范或约束？

**可选收集：**
6. 需要用到哪些工具？（Bash, Read, Write, WebFetch 等）
7. 任务是一步完成还是需要多步？
8. 有没有可以参考的现有工作流？

将收集的需求整理为 `skill-brief.md`。

**暂停**：请用户确认需求摘要。

### Pass 2 — Skill 生成

根据收集的需求，生成 SKILL.md。遵循以下规则：

**description 写作（Ch2 方法论）：**
- 用三步法：What + When + Keywords
- 长度 50-150 字
- 第三人称描述能力
- 包含触发同义词

**指令结构（Ch3 五要素）：**
根据任务复杂度选择要素：

| 需求特征 | 包含的要素 |
|---------|-----------|
| 简单的单步任务 | 步骤序列 + 约束 |
| 有固定输出格式 | + 输出格式/模板 |
| 复杂/多步骤 | + 角色声明 + 判断标准 |

**工作流设计（Ch4）：**
- 如果任务可以一步完成 → 单步 Skill
- 如果任务有 2-3 个阶段 → Multi-Pass（标注暂停点）
- 如果任务有多种模式 → 添加命令表（Ch5）

**示例与锚定（Ch6）：**
- 至少包含 1 个输入/输出示例
- 如果有固定输出格式，添加输出模板
- 如果有常见错误模式，添加 1 个反例

**质量自检（Ch9）：**
- 添加 5-10 项 Quality Checklist
- 检查项必须可验证

输出完整的 SKILL.md 文件。

### Pass 3 — 自我审查

对 Pass 2 生成的 SKILL.md 进行审查，检查以下清单：

```
Skill 元审查清单：
- [ ] description 遵循三步法（What + When + Keywords）
- [ ] description 长度 50-150 字
- [ ] 指令结构有编号步骤
- [ ] 有输出格式或模板
- [ ] 约束条件使用具体数字（不是"适当"、"合理"）
- [ ] 如果超过 100 行，是否需要三层架构？
- [ ] Quality Checklist 每项可验证
- [ ] YAML Frontmatter 格式正确
- [ ] 没有解释 Agent 已知的基础知识
- [ ] 没有重述 Agent 内置工具的使用方法
```

如果有不合格项，修正后输出最终版本。

### Pass 4 — 文件创建

1. 创建 Skill 目录：`skills/<skill-name>/`
2. 写入 SKILL.md
3. 如果需要三层架构，创建 scripts/ 和 reference/ 目录
4. 输出创建摘要

## `/skill-creator review <path>`

读取指定路径的 SKILL.md，按 Ch11 的 7 维度方法论审查：

1. **定位与 description**：精准度评分（1-10）
2. **结构与组织**：是否清晰、是否需要拆分
3. **指令质量**：五要素覆盖情况
4. **工作流设计**：是否需要 Multi-Pass
5. **锚定手段**：示例/模板/反例覆盖度
6. **质量控制**：Checklist 完善度
7. **工具编排**：工具声明是否充分

输出评审报告，包含：
- 各维度评分
- 具体改进建议
- 优先级排序

## 约束

- 生成的 Skill 必须可以直接使用（不需要额外编辑）
- description 不要超过 150 字
- SKILL.md 不要超过 300 行（超过的内容建议拆到辅助文件）
- 示例必须是可理解的（不要用 foo/bar 这种无意义占位符）
- 如果不确定用户需求的某个方面，宁可问清楚也不要猜测

## Quality Checklist

```
- [ ] 生成的 description 遵循三步法
- [ ] 指令包含编号步骤
- [ ] 有至少 1 个示例
- [ ] 约束条件具体可量化
- [ ] Checklist 每项可验证
- [ ] YAML Frontmatter 格式正确
- [ ] 文件已成功写入
- [ ] 目录结构正确
```

## Tool Usage

| Tool | Purpose |
|------|---------|
| AskUserQuestion | Pass 1 需求收集 |
| Read | 审查已有 Skill |
| Write | 输出 SKILL.md 和辅助文件 |
| Bash | 创建目录结构 |
```

## 12.2 元 Skill 的递归之美

注意一个有趣的事实：`skill-creator` 本身就是一个 Skill，它遵循了本书教的所有最佳实践：

- 精准的 description（三步法）
- 命令系统（create / review / improve）
- Multi-Pass 工作流（4 步）
- 质量自检清单
- 工具编排声明

**如果你用 `skill-creator` 来审查 `skill-creator` 本身**，它应该给自己一个不错的分数。这种自指性（self-reference）正是元编程的魅力。

### 对比：lovstudio 的 skill-creator

lovstudio 生态也有自己的 `skill-creator`，但设计思路有显著差异：

```markdown
## lovstudio/skill-creator 的 5 步流程

1. **需求收集**：AskUserQuestion 收集功能、场景、输入输出
2. **独立仓库初始化**：创建 Git 仓库 + README + CHANGELOG + LICENSE
3. **SKILL.md 生成**：包含扩展 Frontmatter（category, version, tags）
4. **测试用例生成**：在 cases/ 目录下创建 2-3 个测试场景
5. **注册到索引**：更新中央 skills.yaml，添加版本徽章到 README
```

关键差异：

| 维度 | 本书的 skill-creator | lovstudio 的 skill-creator |
|------|---------------------|---------------------------|
| 输出单位 | 一个 SKILL.md 文件 | 一个完整的 Git 仓库 |
| 元数据 | 标准 Frontmatter | 扩展 Frontmatter（category, tags, version） |
| 测试 | 自我审查 Checklist | 生成 cases/ 测试目录 |
| 生态集成 | 无 | 自动注册到中央索引 |

lovstudio 的版本更"重"——它不只是创建一个 Skill，而是创建一个**可分发的 Skill 产品**。这反映了不同的使用场景：个人使用 vs 生态分发。

选择哪种取决于你的场景。如果你只是为自己写 Skill，本书的轻量版足够了。如果你要运营一个 Skill 生态或团队标准库，lovstudio 的仓库级 skill-creator 更合适。

## 12.3 用 skill-creator 创建一个 Skill

让我们实际演示：用 skill-creator 创建一个 `changelog-writer` Skill。

```
User: /skill-creator create

Agent: 我来帮你创建一个新的 Skill。先回答几个问题：

1. 这个 Skill 做什么？
User: 根据 Git 提交记录自动生成 CHANGELOG

2. 什么场景下使用？
User: 发版本前，需要更新 CHANGELOG 时

3. 输入是什么？
User: Git 提交历史（从上一个 tag 到 HEAD）

4. 输出是什么格式？
User: Keep a Changelog 格式的 Markdown

5. 有什么约束？
User: 只包含 feat 和 fix 类型的提交，按类型分组

Agent: [生成需求摘要，等待确认]

Agent: [生成 SKILL.md，包含 description + 步骤 + 模板 + checklist]

Agent: [自我审查，确认通过]

Agent: 已创建 skills/changelog-writer/SKILL.md
```

生成的 Skill 会自动包含：
- 精准的 description
- 2-Pass 工作流（收集提交 → 生成 CHANGELOG）
- Keep a Changelog 格式模板
- 5 项 Quality Checklist

## 12.4 社区与分发

你的 Skill 不应该只活在你的电脑上。以下是分发 Skill 的方式——从简单的 Git 仓库到 lovstudio 级别的商业生态。

### 模式 1：简单 Git 仓库

```bash
# 创建一个 Skill 仓库
mkdir my-skills && cd my-skills
git init
cp -r ~/.qoder/skills/commit-message .
cp -r ~/.qoder/skills/code-review .
git add . && git commit -m "Initial skill collection"
git remote add origin git@github.com:you/my-skills.git
git push -u origin main
```

其他人使用：

```bash
git clone git@github.com:you/my-skills.git
cp -r my-skills/commit-message ~/.qoder/skills/
```

### 模式 2：lovstudio 生态架构（进阶）

lovstudio 运营着一个拥有 33 个 Skill 的商业生态 (https://github.com/lovstudio/skills)。他们的架构值得学习：

```
lovstudio/skills/          ← 中央索引仓库
├── README.md              ← 33 个 Skill 的分类展示
├── skills.yaml            ← 机器可读的全局索引
├── any2deck/              ← 每个 Skill 一个子目录（或独立仓库）
│   ├── SKILL.md
│   ├── references/
│   └── cases/             ← 测试用例和示例
├── any2pdf/
├── skill-creator/
├── skill-optimizer/       ← 自动维护生态质量的 Skill
└── ...
```

关键设计决策：

**1. 独立仓库 + 中央索引**：每个 Skill 可以是独立 Git 仓库，通过 `skills.yaml` 统一索引。好处是每个 Skill 可以有独立的版本、Issue、Star。

**2. 分类体系**：

```yaml
# skills.yaml 结构示例
categories:
  - name: 内容创作
    skills: [any2deck, any2pdf, any2video]
  - name: 开发工具
    skills: [skill-creator, skill-optimizer, fill-form]
  - name: 安全与检测
    skills: [anti-wechat-ai-check]
```

**3. 扩展 Frontmatter 标准**：lovstudio 为生态管理扩展了 YAML Frontmatter：

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
  tags: [slides, presentation, deck]
---
```

如果你计划管理 10 个以上的 Skill，这种扩展 Frontmatter 几乎是必须的——它支撑了分类、搜索、版本管理和兼容性声明。

**4. 付费/免费混合模式**：lovstudio 的部分 Skill 是付费的——通过私有仓库分发，只有付费用户能 `git clone`。这是 Skill 商业化的一种可行路径。

**5. 质量自动化**：生态中专门有一个 `skill-optimizer` Skill（见 Ch11），自动审计所有 Skill 的质量并同步版本号。这解决了多 Skill 维护的一致性问题。

### 模式 3：版本管理

无论用哪种分发模式，版本管理都很重要：

```bash
git tag v1.0.0 -m "Initial release: commit-message + code-review"
git push --tags
```

lovstudio 的实践：在 README.md 中用徽章展示版本：

```markdown
![Version](https://img.shields.io/badge/version-2.1.0-blue)
![Compatibility](https://img.shields.io/badge/claude--code-compatible-green)
```

### 安全注意事项

> **Warning**: Skill 可以指导 Agent 执行任意操作（包括运行 Bash 命令、写入文件）。安装第三方 Skill 前，务必审查 SKILL.md 和 scripts/ 的内容。

审查清单：
- [ ] SKILL.md 中没有可疑的命令（如 `curl | bash`）
- [ ] scripts/ 中的脚本没有网络请求到未知地址
- [ ] 没有读取或发送敏感信息（~/.ssh, ~/.aws, 浏览器 cookies）
- [ ] 扩展 Frontmatter 中的 `compatibility` 声明与你的环境匹配

## 12.5 回顾：你的 Skill 工程方法论

12 章的核心要点，浓缩为一页纸：

```
1. Skill = YAML Frontmatter + Markdown 指令
2. description 是最重要的一行——用三步法（What + When + Keywords）
3. 指令要可执行——五要素：角色、步骤、格式、约束、标准
4. 复杂任务用 Multi-Pass——每步一件事，交接文件传递
5. 多种模式用命令路由——一个 Skill 多个入口
6. 示例 > 描述——用输入/输出对锚定行为
7. 超过 300 行用三层架构——SKILL.md + scripts/ + reference/
8. 工具编排要明确——声明每步用什么工具
9. 质量自检要内置——可验证的 Checklist
10. 持续迭代——测试、A/B 对比、诊断、改进
11. 从优秀案例中学习——7 维度解剖法
12. 把方法论编码为元 Skill——让 Agent 帮你写 Skill
```

这 12 条就是你的 **Skill 工程方法论**。无论面对什么领域的 Skill 需求，按这个框架来，你都能写出高质量的 Skill。

## 12.6 Anthropic 官方 Skill-Creator 深度解析

在 12.1 中我们构建了一个简化版的 skill-creator。现在让我们看看 Anthropic 官方版本——一个 485 行的 SKILL.md，代表了 Skill 工程的最高实践水平。

### 架构对比

| 维度 | 本书简化版 | Anthropic 官方版 |
|------|-----------|----------------|
| SKILL.md 行数 | ~100 行 | 485 行 |
| 子 Agent | 无 | 4 个专门化 Agent |
| 测试框架 | 手动 A/B | 完整 eval 系统 + 可视化 |
| 描述优化 | 手动迭代 | 自动化循环（Ch10 已展开） |
| 适用场景 | 个人快速创建 | 团队级/生产级 Skill 开发 |

### 子 Agent 体系

官方版本最显著的特点是引入了专门化的子 Agent：

```
skill-creator (主 Agent)
├── Executor     内联指令    执行测试用例（with-skill / baseline）
├── Grader       agents/grader.md     评估断言是否通过
├── Comparator   agents/comparator.md  盲比较两个版本的输出质量
└── Analyzer     agents/analyzer.md    分析基准数据，发现隐藏模式
```

为什么需要子 Agent？因为**创建 Skill** 和**评估 Skill** 需要不同的心态：

- Executor 需要"忠实执行"——严格按 Skill 指令操作
- Grader 需要"严格判断"——客观评估断言是否通过
- Comparator 需要"盲审"——不知道哪个是新版本哪个是旧版本
- Analyzer 需要"宏观思考"——从统计数据中发现模式

这就是第 9 章讨论的**生成器-验证器隔离**在实践中的体现。

### eval-viewer 可视化系统

官方版本包含一个 HTML 可视化查看器，用于辅助人工评审：

- **Outputs 标签页**：逐个查看测试用例的输出，支持反馈输入
- **Benchmark 标签页**：定量统计对比（pass rate、时间、token 用量）
- **Previous Output**（迭代 2+）：折叠显示上一轮输出
- **Previous Feedback**（迭代 2+）：显示上一轮的评论

这个查看器解决了一个关键问题：在终端中阅读和对比大量测试输出非常困难。可视化界面让审查过程更高效。

### 何时使用官方版 vs 简化版

- **个人使用、快速原型**：用简化版。几分钟内完成，足够好用
- **团队 Skill 标准库**：用官方版。系统化的评估确保质量一致
- **社区发布的 Skill**：用官方版。自动化测试和优化确保触发率和可靠性

## 12.7 自动化 Skill 发现：从失败中学习

前面的章节都是关于**人工设计** Skill 的方法论。但学术前沿正在探索另一条路径：**让 Agent 自动发现需要什么 Skill**。

### EvoSkill：从失败轨迹提炼 Skill

EvoSkill 项目的核心洞察：当 Agent 在某个任务上反复失败时，这个失败本身就是一个信号——说明这个任务需要一个专门的 Skill。

工作流程：
1. Agent 尝试执行任务 → 失败
2. 分析失败轨迹——哪里出了问题？
3. 从失败中提炼出一个新 Skill——"下次遇到这类问题，按以下步骤处理"
4. 新 Skill 加入库中 → Agent 下次遇到类似问题时自动加载

### EvoSkills：生成器-验证器协同进化

EvoSkills（注意多了一个 s）在 EvoSkill 基础上引入了我们在第 9 章讨论的**生成器-验证器隔离**：

```
Generator Agent: 创建/改进 Skill
Verifier Agent: 独立测试 Skill 的效果
                 （不知道 Skill 的创建过程）
```

实验结果：自检模式（同一个 Agent 创建+测试）通过率 32%；隔离验证模式通过率 75%。

### SkillForge：从企业工单自动生成 Skill

SkillForge 项目更进一步——它从企业的客服工单和支持记录中自动提炼 Skill：

1. 分析历史工单，找出重复的问题模式
2. 为每种模式生成一个 Skill 草稿
3. 用四维诊断（知识/工具/澄清/语气）评估和改进
4. 人工审核后上线

### 对 Skill 工程的启示

你不需要部署这些学术系统。但它们的核心洞察可以直接应用：

**记录 Agent 做得不好的场景**。每次你发现 Agent 在某个任务上表现不佳，记下来。这些场景就是**潜在的 Skill 种子**：

```markdown
## Skill 种子清单

- Agent 总是把 YAML 缩进搞错 → 需要 yaml-formatter Skill
- Agent 生成的 SQL 查询有 N+1 问题 → 需要 sql-optimizer Skill
- Agent 写的错误信息对用户不友好 → 需要 error-message Skill
```

失败不是浪费——它是 Skill 发现的最佳信号。

## 12.8 展望：全球 Skill 生态

Skill 生态正在快速发展。以下是截至 2026 年的全景图。

### 主要 Skill 仓库

| 平台 | 规模 | 特点 |
|------|------|------|
| Anthropic 官方 (anthropics/skills) | 5 个生产级 Skill | 黄金标准参考实现 |
| OpenClaw | 5,400+ Skill | 最大的社区生态 |
| Vercel Agent Skills | 25K+ Stars | Scripts-First 原则的实践典范 |
| Orchestra Research | 7K+ Stars | 双循环架构、完全自主运行的前沿探索 |
| OpenSkills | 9K+ Stars | 跨平台兼容性框架 |
| skill-of-skills | 686+ 条目 | 最全的 Skill 目录/索引 |
| lovstudio | 33 个精品 Skill | 商业化运营的先行者 |

### 跨平台兼容性

SKILL.md 格式已被 9 个主要平台采纳——这个事实大幅提升了学习 Skill 工程的价值：

- **Claude Code** — Anthropic 官方
- **Qoder** — 本书的主要实践平台
- **Codex CLI** — OpenAI 的命令行 Agent
- **Gemini CLI** — Google 的命令行 Agent
- **GitHub Copilot** — 通过 AGENTS.md 兼容
- **Cursor** — 通过 .cursor/rules 兼容
- **Windsurf** — 通过 .windsurfrules 兼容
- **Cline** — 通过 .clinerules 兼容
- **Roo Code** — 通过 .roo/rules 兼容

这意味着你学会的 Skill 写作方法论**不绑定任何一个平台**。

### 2026 四大趋势

**趋势 1: 完全自主执行**

Orchestra Research 的 Autoresearch 模式已经展示了未来——Agent 不再每一步都请求许可，而是**自主运行 + 频繁汇报进度**。Skill 需要支持这种模式：不需要暂停点的长流程、状态持久化以支持中断恢复。

**趋势 2: 多 Agent 编排**

复杂任务不再由单个 Agent 完成，而是多个 Agent 协作。Anthropic 的子 Agent 体系是早期形态；未来的 Skill 可能需要定义"我可以调用哪些其他 Skill"的编排接口。

**趋势 3: Agentic IDE 融合**

Skill 不再是独立于 IDE 的配置文件。它正在融入开发工作流——从 commit hook、PR review、CI/CD pipeline 到代码补全，都可以由 Skill 驱动。

**趋势 4: 领域纵深**

早期 Skill 多为通用工具（代码审查、文档生成）。趋势是向**特定领域纵深**——Orchestra Research 的 ML 研究 Skill 体系、lovstudio 的垂直分类生态都是这个方向。

### 正在涌现的生态模式

**商业生态**：lovstudio 运营着 33 个 Skill 的分类生态，部分付费分发——这可能是 Skill 生态商业化的先兆。

**质量自动化**：lovstudio 的 `skill-optimizer` 证明了 Skill 质量可以自动审计和维护。未来可能出现通用的 Skill Lint 工具——就像 ESLint 之于 JavaScript。

**自动 Skill 发现**：EvoSkill 和 SkillForge（12.7）展示了从失败中自动提炼 Skill 的可能性。这意味着 Skill 库可以随着 Agent 的使用而自动增长。

作为一个掌握了 Skill 工程方法论的人，你不仅能为自己写 Skill，还能：
- 为团队建立 Skill 标准库
- 评估和改进社区 Skill 的质量
- 设计新的 Skill 模式和架构
- 参与 Skill 生态的建设
- 运营商业级 Skill 服务

**Skill 工程不是一个技巧——它是 AI 时代的一种新型软件工程能力。**

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 自己写每一个 Skill | Agent 帮你创建 Skill |
| 方法论在脑子里 | 方法论编码为可执行的元 Skill |
| Skill 只在本地 | 理解分发、生态和全球版图 |
| 不知道学术前沿在做什么 | 了解自动 Skill 发现和协同进化 |

**Cumulative capability**: 你拥有了一个完整的 Skill 工具箱（12 个 Skill），掌握了 Skill 工程的完整方法论，以及一个能帮你创建新 Skill 的元 Skill。你还了解了 Anthropic 官方架构和全球生态版图。

## Try It Yourself

> 完整代码见 `code/track-1/ch12-skill-creator/`（= Track 2 v12 最终版），可直接复制到 `~/.qoder/skills/` 使用。
>
> **Track 2 完结**：查看 `code/track-2/v12-final/SKILL.md` 末尾的"演化历程"表，
> 回顾 skill-creator 从 13 行到 599 行的完整进化。也可以直接 diff v01 和 v12 感受全貌：
> `diff code/track-2/v01-basic/SKILL.md code/track-2/v12-final/SKILL.md`

1. **Verify**: 用 `skill-creator` 创建一个你一直想要的 Skill（比如 `meeting-notes`、`code-migration`、`bug-report-writer`）。
2. **Extend**: 用 `skill-creator review` 审查 `skill-creator` 本身。根据审查结果改进它——这是一个递归！
3. **Explore**: 把你在本书中创建的所有 Skill 打包成一个 Git 仓库，分享给你的团队或社区。
4. **Seed List**: 开始记录你的"Skill 种子清单"——每次 Agent 做得不好的场景，记下来，每月从中选一个种子创建新 Skill。

## Summary

- **元 Skill** 把 Skill 创作方法论编码为可执行的 Skill
- `skill-creator` 通过 4-Pass 流程创建 Skill：需求收集 → 生成 → 审查 → 写入
- Anthropic 官方 skill-creator 用 **4 个子 Agent** 实现了创建-评估的完整隔离
- **自动 Skill 发现**：从失败轨迹提炼 Skill（EvoSkill）、生成器-验证器协同进化（EvoSkills）、从工单生成 Skill（SkillForge）
- SKILL.md 格式已被 **9 个主要平台**采纳——Skill 工程是跨平台的能力
- Skill 通过 **Git 仓库**分发，安装前务必审查安全性
- 12 章浓缩为 12 条方法论——这就是你的 Skill 工程框架
- **Skill 工程是 AI 时代的新型软件工程能力**

## Further Reading

- Anthropic 官方 Skill 文档：平台级的 Skill 规范和 API
- Agent Skills 开放标准：agentskills.io/specification
- lovstudio/skills：33 个商业级 Skill 的分类生态
- skill-of-skills：最全的 Skill 目录
- EvoSkill / EvoSkills：自动 Skill 发现和协同进化的学术论文
- SkillForge：从企业工单自动生成 Skill 的方法论
- 本书 GitHub 仓库：所有 Skill 的完整源码和演进历史
