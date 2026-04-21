# Chapter 2: Description：最重要的一行

> **Motto**: "Agent 看不到你的 Skill 内容，只看到 description"

> 你已经写出了第一个 Skill，Agent 也成功加载了它。但你有没有想过：Agent 是怎么决定"现在需要加载这个 Skill"的？答案藏在一个你可能随手写完的字段里——`description`。本章你将深入理解 description 的工作原理，并通过反复实验，掌握写出精准 description 的技巧。

![Chapter 2: Description：最重要的一行](images/ch02-description.png)

## The Problem

你写了一个 `code-review` Skill，description 是这样的：

```yaml
---
name: code-review
description: 代码相关的技能
---
```

然后你让 Agent "帮我审查 app.py 的代码质量"。

Agent 没有加载你的 Skill。它用自己内置的知识做了一份平庸的审查。

你很困惑——Skill 明明在那里，为什么 Agent 不用？

问题出在 description。"代码相关的技能"这六个字太模糊了。Agent 在扫描到这个描述时，没有足够的信息判断它和"代码审查"之间的关系。毕竟，"代码相关"可以是写代码、删代码、格式化代码、生成文档——Agent 不确定，就选择不加载。

description 是 Agent 在 Layer 1 唯一能看到的信息。如果这一行写不好，后面的指令写得再完美也没用——因为 Agent 根本不会去读它们。

## The Solution

我们需要把 description 当作一个**搜索引擎的索引词**来对待。它的目标不是"描述 Skill 是什么"，而是"让 Agent 在正确的时机匹配到这个 Skill"。

这意味着 description 需要回答三个问题：

1. **What**: 这个 Skill 做什么？（动作 + 对象）
2. **When**: 什么场景下应该使用？（触发条件）
3. **Keywords**: 用户可能用什么词来表达需求？（覆盖面）

## 2.1 description 的工作原理

当 Agent 启动时，它把所有 Skill 的 description 拼接成一段文本，放在自己的上下文里：

```
可用技能（用 load_skill 工具按需加载）:
  - code-review: 审查代码质量，检查安全、性能、可读性问题...
  - quick-fix: 快速修复代码中的小 Bug...
  - commit-msg: 生成规范的 Git 提交信息...
```

当用户发送请求时，LLM 会"阅读"这段列表，然后做一个判断：当前请求是否需要加载某个 Skill？

这个判断不是关键词匹配——它是语义理解。LLM 理解"帮我看看这段代码有没有问题"和"审查代码质量"是同一个意思，即使用词完全不同。

但语义理解也有边界。如果 description 太模糊（"代码相关"），LLM 的置信度不够高，就不会触发加载。如果 description 太窄（"检查 Python 函数的 type hints"），那用户说"审查代码"时也不会匹配。

**关键洞察**：description 不是给人读的文档——它是给 LLM 读的触发条件。你需要站在 LLM 的角度思考：看到这段描述和用户的请求，我能不能确定它们匹配？

### Token 预算

每个 Skill 的 description 在 Layer 1 大约占 50-100 tokens。这意味着：

- 20 个 Skill 总共只占 ~2000 tokens
- description 的长度上限是 1024 字符（约 300 中文字）
- 但实际上 50-100 字就足够了——太长反而稀释信号

## 2.2 好的 description vs 坏的 description

让我们看 5 组真实的对比。每一组都是同一个 Skill 的两个 description 版本：

### 对比 1：代码审查

```yaml
# 坏
description: 代码相关的技能

# 好
description: 审查代码质量，检查常见问题（安全、性能、可读性），提供改进建议。当用户请求代码审查、review、CR 时使用。
```

坏在哪里？"代码相关"覆盖面太广——写代码、读代码、删代码都是"代码相关"。LLM 无法从中判断这个 Skill 是干什么的。

好在哪里？
- "审查代码质量"——明确的动作 + 对象
- "（安全、性能、可读性）"——具体的检查维度，帮助 LLM 理解深度
- "当用户请求代码审查、review、CR 时使用"——列出了触发关键词

### 对比 2：提交信息

```yaml
# 坏
description: 帮助写 Git 相关的东西

# 好
description: 生成规范的 Git commit message。分析 staged changes，按照 Conventional Commits 格式生成提交信息。当用户提交代码或请求写 commit message 时使用。
```

坏在哪里？"Git 相关的东西"可以是 branch 操作、merge 冲突解决、rebase——太多可能性。

好在哪里？
- "生成规范的 Git commit message"——精确到具体产出
- "分析 staged changes"——描述了输入
- "Conventional Commits 格式"——指定了规范

### 对比 3：测试生成

```yaml
# 坏
description: 测试

# 好
description: 为 Python/TypeScript 函数生成单元测试。分析函数签名和行为，生成覆盖正常路径、边界条件和错误处理的测试用例。使用 pytest/vitest 框架。
```

一个字的 description 等于没有 description。

### 对比 4：文档生成

```yaml
# 坏
description: 可以写各种文档

# 好
description: 为 REST API 端点生成 OpenAPI 格式的文档。分析路由代码，提取参数、响应格式、错误码，生成结构化 API 文档。
```

"各种文档"让 LLM 在任何涉及文档的请求中都可能加载这个 Skill——包括写 README、写注释、写用户手册。这不是你想要的。精确描述"什么类型的文档"才能避免误触发。

### 对比 5：部署

```yaml
# 坏
description: 部署应用

# 好
description: 检查应用的部署就绪状态。验证环境变量、依赖版本、数据库迁移、健康检查端点，生成部署前 checklist。当用户准备部署或想确认部署条件时使用。
```

"部署应用"暗示这个 Skill 会执行部署——但它实际上只是检查就绪状态。好的 description 准确描述 Skill**实际做的事**，而不是它所属的领域。

## 2.3 三步写 description 法

经过上面的对比，我们总结出一个简单的方法论：

### Step 1: What — 这个 Skill 做什么？

用"动词 + 宾语"的格式写出核心动作。

```
审查代码质量
生成 Git commit message
为函数生成单元测试
检查部署就绪状态
```

> **Warning**: 避免使用"帮助"、"处理"、"管理"这类模糊动词。"帮助用户处理代码问题"不如"审查代码质量"清晰。

### Step 2: When — 什么时候使用？

添加触发条件。这可以是：
- 用户可能说的话："当用户请求代码审查时"
- 任务类型："当需要生成 API 文档时"
- 同义词覆盖："review、CR、code review"

```
审查代码质量，检查安全/性能/可读性问题。当用户请求代码审查、review、CR 时使用。
```

### Step 3: How — 补充关键细节

如果有空间，添加帮助 LLM 理解深度和范围的细节：

- 输入是什么？（"分析 staged changes"）
- 输出是什么？（"生成 Conventional Commits 格式的提交信息"）
- 使用什么规范/工具？（"使用 pytest 框架"）

```
审查代码质量，检查常见问题（安全、性能、可读性），提供改进建议和严重度评级。当用户请求代码审查、review、CR 时使用。
```

> **Tip**: 把你的 description 读给一个不了解这个 Skill 的人听。如果他能准确说出"这个 Skill 是做什么的"和"什么时候应该用它"，你的 description 就写得足够好了。

## 2.4 Description 的隐形陷阱：欠触发问题

学会了三步法后，你可能会倾向于写非常精确的 description——毕竟精确意味着不会误触发。但 Anthropic 在大规模实践中发现了一个反直觉的问题：

> **模型倾向于"欠触发"（under-trigger）——在应该使用 Skill 的时候不去使用它。**

为什么？因为 Agent 只会在它**无法独立完成任务**时才会咨询 Skill。对于简单的请求，即使 description 完美匹配，Agent 也可能认为"我自己能搞定"而跳过 Skill。

### "Pushy" 策略

Anthropic 的建议是让 description 写得"稍微 pushy（积极）一些"——覆盖面比你直觉中的要更广：

```yaml
# 保守的 description（容易欠触发）
description: How to build a simple dashboard to display internal data.

# Pushy 的 description（减少欠触发）
description: >
  How to build a simple fast dashboard to display internal data.
  Make sure to use this skill whenever the user mentions dashboards,
  data visualization, internal metrics, or wants to display any kind
  of data, even if they don't explicitly ask for a "dashboard."
```

注意 pushy 版本做了什么：
- **扩展了触发词**：dashboards, data visualization, internal metrics
- **降低了触发门槛**：even if they don't explicitly ask for a "dashboard"
- **覆盖了间接表述**：wants to display any kind of data

### 何时 Pushy，何时保守

| Skill 类型 | 推荐策略 | 原因 |
|-----------|---------|------|
| 强制规范类（commit-message, code-review） | Pushy | 如果不触发，用户会得到不符合团队规范的输出 |
| 工具类（pdf, docx, xlsx） | 适度 Pushy | 这类任务 Agent 通常能自己做，但 Skill 版本更好 |
| 辅助类（brainstorm, explain） | 保守 | 误触发的干扰比漏触发的损失更大 |

> **Tip**: 如果你发现一个 Skill 经常不被加载，先检查 description 是否太保守，然后再考虑是否是指令问题。欠触发是 Skill 系统最常见的 failure mode。

## 2.5 案例：code-review 的 description 三版演进

让我们通过一个完整的迭代过程，看 description 如何从 v1 进化到 v3。

### v1: 最初版本

```yaml
---
name: code-review
description: 代码审查
---
```

两个字。Agent 的反应：偶尔加载，偶尔不加载。当用户明确说"审查代码"时能匹配，但说"帮我看看这段代码有没有问题"时就不一定了。

**问题诊断**：太短，缺少上下文。LLM 需要更多信息来判断匹配置信度。

### v2: 加了细节

```yaml
---
name: code-review
description: 审查代码质量，检查常见问题，提供改进建议
---
```

进步了——"审查代码质量"是清晰的动作，"检查常见问题"扩展了范围，"提供改进建议"说明了输出。

但测试发现：当用户说"这段代码安全吗？"时，Agent 不会加载。因为 description 里没有提到"安全"。

**问题诊断**：缺少具体的检查维度，也缺少触发关键词。

### v3: 精准版本

```yaml
---
name: code-review
description: 审查代码质量，检查常见问题（安全、性能、可读性），提供改进建议。当用户请求代码审查、review、CR、检查代码质量时使用。
---
```

这个版本在以下所有请求中都能正确触发：

- "帮我审查 app.py"
- "review 一下这段代码"
- "这段代码有安全问题吗？"
- "帮我做个 CR"
- "检查一下代码质量"

关键改进：
1. 括号里列出了具体维度（安全、性能、可读性），覆盖了用户可能从任一维度提问
2. 最后的触发词列表（审查、review、CR、检查代码质量）覆盖了多种表述方式

## 2.6 Karpathy 的 description 哲学

Andrej Karpathy 是 Skill 社区的早期倡导者。他的 Skill 设计哲学可以用一句话概括：

**"一个好的 Skill 就是一个好的 SOP（标准操作流程）。"**

观察 Karpathy 风格的 Skill，他们的 description 有几个共同特点：

1. **功能导向**：描述 Skill "做什么"，而不是 Skill "是什么"

   ```yaml
   # Karpathy 风格
   description: Write comprehensive unit tests for Python functions, covering edge cases and error paths.

   # 不好的写法
   description: A skill for unit testing.
   ```

2. **简洁但完整**：一句话包含动作、对象、关键细节

3. **第三人称**：描述 Skill 的能力，而不是对 Agent 下命令

   ```yaml
   # 好: 描述能力
   description: Generate conventional commit messages by analyzing git diff output.

   # 不好: 下命令
   description: You should generate commit messages when asked.
   ```

4. **不解释原理**：description 不需要说"为什么"需要这个 Skill，只需要说"它做什么"

> **Note**: Karpathy 的 Skill 设计理念和他对 AI 系统的整体思考一致——简洁、实用、不过度工程。如果你能用 30 个词写完 description，就不要用 60 个。

## 2.7 常见的 description 反模式

避免以下错误：

### 反模式 1: 太模糊

```yaml
description: 帮助开发
```

问题：几乎所有开发相关的请求都可能匹配，导致频繁误触发。

### 反模式 2: 太技术化

```yaml
description: 实现基于 AST 解析的静态代码分析，利用 tree-sitter 语法树遍历检测潜在的代码质量问题
```

问题：用户不会说"我需要 AST 解析"。description 应该用用户的语言，而不是实现细节的语言。

### 反模式 3: 包含时效性信息

```yaml
description: 按照 2024 年最新的 React 19 规范审查前端代码
```

问题：版本号会过时。description 应该描述永恒的能力，而不是绑定到特定版本。

### 反模式 4: 复制正文内容

```yaml
description: 审查代码质量。首先读取文件，然后检查安全性（SQL 注入、XSS、CSRF），接着检查性能（N+1 查询、不必要的循环），然后检查可读性（命名规范、函数长度），最后输出格式化的报告，包含严重度、文件路径、问题描述和改进建议。
```

问题：description 不是指令的摘要——它是触发条件。不需要包含执行细节。

### 反模式 5: 多个不相关的功能

```yaml
description: 审查代码质量，生成测试用例，编写 API 文档，重构代码结构
```

问题：违反单一职责。如果一个 Skill 做四件事，它应该被拆成四个 Skill。混合的 description 会导致错误的触发——用户想写文档时加载了审查指南。

## 2.8 一个 description 检查清单

每次写完 description，用以下清单自检：

```
- [ ] 包含明确的动作（审查/生成/检查/创建）
- [ ] 包含明确的对象（代码/文档/测试/配置）
- [ ] 描述了触发场景或关键词
- [ ] 长度在 50-150 字之间
- [ ] 不包含实现细节
- [ ] 不包含时效性信息
- [ ] 用用户的语言写，不用技术实现的语言
- [ ] 只描述一个核心功能（单一职责）
```

## 2.9 预告：自动化 Description 优化

本章的技巧都是手动的——你根据经验和检查清单写 description，然后人工测试触发率。但 Anthropic 的 Skill-Creator 提供了一个更系统的方法：**自动化 description 优化循环**。

核心思路是：

1. 为你的 Skill 生成 20 个评估查询（10 个 should-trigger + 10 个 should-not-trigger）
2. 把查询按 60/40 分成训练集和测试集
3. 每个查询运行 3 次，统计触发率
4. 分析失败案例，改进 description
5. 按测试集分数选最佳版本（防过拟合）
6. 最多迭代 5 轮

这个方法特别值得注意的一点：should-not-trigger 的查询必须是**近似误匹配**（和 Skill 相关但不应触发），而非明显无关的请求。因为明显无关的查询不会触发任何 Skill，测试它们毫无意义。

我们会在第 10 章《测试与调优》中详细展开这个方法。如果你现在就想优化 description，先用本章的手动方法——它已经能覆盖 80% 的场景。

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| description 随手写几个字 | 用三步法写出精准的 description |
| 不理解为什么 Skill 不被加载 | 理解 description 是唯一的触发条件 |
| 没有评估 description 质量的标准 | 掌握检查清单和反模式识别 |
| 不知道 Skill 为什么"该触发却没触发" | 理解欠触发问题和 pushy 策略 |

**Cumulative capability**: 你现在能写出精准的 description，让 Skill 在正确的时机被正确地加载。`code-review` Skill 从 v1 演进到了 v3。

## Try It Yourself

> 完整代码见 `code/track-1/ch02-code-review/`，可直接复制到 `~/.qoder/skills/` 使用。
>
> **Track 2 演进**：对比 `code/track-2/v01-basic/SKILL.md` 和 `code/track-2/v02-description/SKILL.md` 的 diff，
> 观察 description 从 5 字增长到 100+ 字的变化。

1. **Verify**: 为你的 `quick-fix` Skill 重写 description，使用三步法。然后用 5 种不同的措辞请求修 Bug（"帮我修个 Bug"、"这里有个错误"、"fix this issue"、"代码报错了"、"这个函数有问题"），记录每种措辞是否触发了 Skill 加载。

2. **Extend**: 创建 `code-review` Skill 的 v1、v2、v3 三个版本（放在不同目录下），同样的审查请求，分别测试三个版本的触发率。记录数据。

3. **Explore**: 打开 skill-of-skills 目录 (https://github.com/the911fund/skill-of-skills)，随机浏览 10 个 Skill 的 description。用本章的检查清单评估它们，找出 3 个好的和 3 个可以改进的。

4. **Pushy Test**: 选一个你现有的 Skill，用 pushy 策略重写 description。对比重写前后的触发率——特别是那些间接表述（用户没有明确说出 Skill 名称）的场景。

## Summary

- description 是 Agent 在 Layer 1 唯一能看到的信息——它决定了 Skill 的**加载时机**
- 好的 description 回答三个问题：**What**（做什么）、**When**（何时用）、**Keywords**（触发词）
- description 不是文档——它是**给 LLM 读的触发条件**
- **欠触发是最常见的问题**——模型倾向于"不加载"而非"误加载"，description 应适度 pushy
- 常见反模式：太模糊、太技术化、包含时效性信息、复制正文、多功能混合
- Karpathy 的 description 哲学：功能导向、简洁完整、第三人称、不解释原理
- 用 **description 检查清单** 自检每一个新写的 description
- 自动化 description 优化循环（详见第 10 章）可以系统化地提升触发准确率

## Further Reading

- Anthropic 官方文档：Skill Authoring Best Practices — Description 部分
- skill-of-skills 目录：浏览 686+ Skill 的 description 写法
- 《信息检索导论》(Manning et al.)：理解为什么"精确率 vs 召回率"的权衡适用于 description 设计
- 第 10 章《测试与调优》——description 自动化优化循环的完整方法
