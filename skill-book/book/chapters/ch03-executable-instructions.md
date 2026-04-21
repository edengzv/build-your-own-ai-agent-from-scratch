# Chapter 3: 可执行的指令

> **Motto**: "模糊的指令产生模糊的结果"

> description 让 Skill 被正确加载——这解决了"什么时候用"的问题。但 Skill 正文的指令质量决定了 Agent 执行得好不好——这是"怎么用"的问题。本章你将学会区分"模糊指令"和"可执行指令"，并掌握结构化指令写作的五个要素。

![Chapter 3: 可执行的指令](images/ch03-executable-instructions.png)

## The Problem

你写了一个生成 Git 提交信息的 Skill。正文是这样的：

```markdown
# Commit Message Generator

帮用户写好的 Git 提交信息。要求信息清晰、规范、有用。
```

Agent 加载了这个 Skill，然后生成了这样的提交信息：

```
Updated some files and fixed a bug
```

这不是你想要的。你想要的是类似这样的：

```
fix(auth): resolve token expiration check in middleware

The JWT validation was comparing timestamps in different timezones,
causing premature token rejection for users in UTC+ regions.

Closes #1234
```

问题出在哪里？你的指令太模糊了。"写好的"——什么叫好？"清晰"——怎样算清晰？"规范"——什么规范？Agent 没有读心术，它只能从你写的指令中获取信息。你给了三个形容词，但没有给任何可操作的步骤。

## The Solution

可执行的指令和模糊的指令之间的区别，就像菜谱和"做一道好吃的菜"之间的区别。菜谱告诉你：用什么食材、放多少量、什么顺序、火候多大、做多久。"做一道好吃的菜"则把所有决策都留给执行者。

我们的目标是把 Skill 的指令写成**菜谱**——具体、有序、可验证。

## 3.1 可执行性光谱

指令的可执行性不是非黑即白的，它是一个光谱：

```
模糊              ←──────────────────────→              精确
"写好的代码"    "遵循规范"    "按这些步骤"    "用这个模板"    "运行这个脚本"
  ↑               ↑              ↑              ↑              ↑
 Agent 全靠猜    Agent 部分猜   Agent 有方向   Agent 有模板    完全确定性
```

你不一定总是需要最精确的那端。关键是根据**任务的脆弱度**选择合适的精确度。我们把这叫做**自由度匹配**——不同类型的任务需要不同程度的指令约束。

### 窄桥型 vs 开阔地型

想象两种场景：一座独木桥（窄桥），你必须精确地走每一步；一片草地（开阔地），你只需要知道方向就行。Skill 的指令设计也一样：

| 任务类型 | 自由度 | 指令风格 | 典型场景 |
|---------|--------|---------|---------|
| **窄桥型** — 确定性操作 | 低 | 精确命令序列，每步一个动作 | 数据库迁移、安全修复、部署脚本、格式化输出 |
| **开阔地型** — 知识性任务 | 高 | 方向性指引，给目标不给路径 | 代码审查、设计方案、创意写作、架构建议 |
| **工具依赖型** — 条件分支 | 中 | 条件判断 + 分支路径 | 多平台适配、环境检测、模式选择 |

> **Tip**: 判断方法很简单——如果输出格式错误会导致流程中断（比如提交信息不符合 CI/CD 规则），那就是窄桥型任务，需要精确模板。如果输出是给人阅读的（比如代码审查意见），那就是开阔地型，给方向就好。

窄桥型任务的指令看起来像操作手册：

```markdown
## 执行步骤
1. 运行 `git diff --cached` 查看 staged changes
2. 确定类型：feat / fix / refactor / docs / test / chore
3. 按模板生成：`<type>(<scope>): <summary>`
```

开阔地型任务的指令看起来像设计简报：

```markdown
## 审查方向
- 重点关注安全性和正确性
- 风格问题只在严重影响可读性时才提
- 给出具体的改进建议，而非笼统的评论
```

选错自由度的后果：窄桥型任务给太多自由，Agent 会产出不可预测的格式；开阔地型任务约束太死，Agent 会变成一个无聊的模板填充机。

## 3.2 模糊指令 vs 可执行指令

让我们用 `commit-message` Skill 做一个完整的对比。

### 模糊版本

```markdown
---
name: commit-message
description: 生成规范的 Git commit message。分析 staged changes，按 Conventional Commits 格式输出。
---

# Commit Message Generator

帮用户写好的 Git 提交信息。要求信息清晰、规范、有用。

注意事项：
- 信息要简洁
- 要说明改了什么
- 格式要规范
```

问题清单：
- "好的"——没定义标准
- "清晰"——没给示例
- "规范"——没指定哪个规范
- "简洁"——多短算简洁？
- "说明改了什么"——怎么分析？看 diff？看文件名？

### 可执行版本

```markdown
---
name: commit-message
description: 生成规范的 Git commit message。分析 staged changes，按 Conventional Commits 格式输出。当用户提交代码或请求生成 commit message 时使用。
---

# Commit Message Generator

分析 Git staged changes，生成符合 Conventional Commits 规范的提交信息。

## 执行步骤

1. 运行 `git diff --cached` 查看 staged changes
2. 分析改动，确定：
   - **类型**：feat / fix / refactor / docs / test / chore / style / perf
   - **范围**：受影响的模块或组件名（如 auth, api, ui）
   - **摘要**：一句话描述改动（不超过 50 字符，不以句号结尾）
3. 如果改动较复杂，添加 body 段落（空一行后）解释 **为什么** 做这个改动
4. 如果有关联的 Issue，添加 footer：`Closes #123`

## 输出格式

```
<type>(<scope>): <summary>

<body: 解释为什么做这个改动，而不是做了什么>

<footer: Closes #xxx>
```

## 示例

输入（git diff 结果）：
```diff
--- a/src/auth/middleware.js
+++ b/src/auth/middleware.js
@@ -42,7 +42,7 @@
-  const isExpired = token.exp < Date.now()
+  const isExpired = token.exp * 1000 < Date.now()
```

输出：
```
fix(auth): correct token expiration timestamp comparison

JWT exp field uses seconds since epoch, but Date.now() returns
milliseconds. Multiplying by 1000 before comparison prevents
premature token rejection.
```

## 约束

- 标题行不超过 50 字符
- body 每行不超过 72 字符
- 不要在标题末尾加句号
- 使用祈使语气（"add" 而非 "added"、"fix" 而非 "fixed"）
- 如果 staged changes 为空，提醒用户先 `git add`
- 如果改动涉及多个不相关的功能，建议用户拆分为多次提交
```

对比一下：模糊版本 20 行，可执行版本 50 行。但可执行版本的每一行都在消除歧义、锚定行为。

## 3.3 结构化指令的五个要素

通过分析大量优秀 Skill 的正文，我总结出结构化指令的五个核心要素：

### 要素 1: 角色声明

告诉 Agent 它在这个 Skill 中扮演什么角色。这不是必须的，但对于需要特定"人格"的 Skill 很有用。

```markdown
# 好的角色声明
你是一个严格的代码审查者。你的目标是发现潜在的 Bug 和安全漏洞，而不是挑剔代码风格。

# 不好的角色声明
你是一个非常厉害的 10x 工程师，世界上最好的代码审查专家。
```

好的角色声明是**功能性的**——它定义了行为边界（"严格"、"发现 Bug 而非挑剔风格"）。坏的角色声明是**装饰性的**——"非常厉害"不会让 Agent 表现更好。

> **Warning**: 不要把角色声明当作万灵药。Agent 的表现主要取决于指令的质量，而不是你给它安排了什么角色。

### 要素 2: 步骤序列

编号的步骤列表，每步一个明确的动作。这是 Skill 正文中最重要的部分。

```markdown
## 执行步骤

1. 读取目标文件
2. 识别所有公开函数和类
3. 对每个公开函数：
   a. 检查是否有 docstring
   b. 如果没有，根据函数签名和实现生成 docstring
   c. 如果有，检查是否与实现一致
4. 用 Edit 工具插入/更新 docstring
5. 输出修改摘要
```

步骤序列的写法原则：
- **每步一个动作**：不要把两件事塞在一步里
- **动词开头**：读取、检查、生成、输出
- **顺序清晰**：前一步的输出是后一步的输入
- **可跳过的条件**：用 "如果...则..." 处理分支

### 要素 3: 输出格式

明确告诉 Agent 输出应该长什么样。可以是模板、示例、或格式描述。

```markdown
## 输出格式

对每个问题使用以下格式：

[severity: high | medium | low]
文件: <file_path>
行数: <start_line>-<end_line>
问题: <一句话描述问题>
建议: <具体的修复建议>
```

输出格式越精确，输出的一致性越高。第 6 章会深入讨论模板锚定技巧。

### 要素 4: 约束条件

告诉 Agent "不要做什么"和"边界在哪里"。约束条件消除了 Agent 自行决策时可能犯的错误。

```markdown
## 约束

- 只审查 staged 文件，不要审查未暂存的改动
- 不要自动修复问题——只报告和建议
- 每个文件最多报告 10 个问题，优先报告高严重度的
- 如果无法判断严重度，标记为 medium
```

约束条件的写法：
- **具体的数字**："最多 10 个"而不是"不要太多"
- **明确的边界**："只审查 staged 文件"而不是"注意范围"
- **默认行为**："如果无法判断，标记为 medium"

### 要素 5: 判断标准

告诉 Agent 怎么判断自己做得好不好。这是高级技巧，但对提升输出质量有显著效果。

```markdown
## 质量标准

一个好的提交信息：
- 看了标题就知道改了什么（不需要看 diff）
- body 解释的是"为什么"而不是"做了什么"
- 回顾时能理解当时的决策背景
```

判断标准不是检查清单（那是第 9 章的内容），而是**质量的定义**——让 Agent 知道"好"长什么样。

## 3.4 实战：commit-message Skill 完整版

综合五个要素，这是最终的 `commit-message` Skill：

```markdown
---
name: commit-message
description: 生成规范的 Git commit message。分析 staged changes，按 Conventional Commits 格式输出。当用户提交代码或请求生成 commit message 时使用。
---

# Commit Message Generator

你是一个注重清晰沟通的工程师。你的目标是写出让三个月后的自己（或同事）都能立刻理解的提交信息。

## 执行步骤

1. 运行 `git diff --cached --stat` 查看 staged 文件列表
2. 如果没有 staged changes，提醒用户先 `git add`，然后停止
3. 运行 `git diff --cached` 查看详细改动
4. 分析改动，确定：
   - **类型**：从以下选择最匹配的
     - `feat`: 新功能
     - `fix`: Bug 修复
     - `refactor`: 重构（不改变行为）
     - `docs`: 文档变更
     - `test`: 测试相关
     - `chore`: 构建/配置/依赖
     - `style`: 格式调整（空格、分号等）
     - `perf`: 性能优化
   - **范围**：受影响的模块/目录名
   - **摘要**：一句话描述核心改动
5. 判断是否需要 body：如果改动的"为什么"不显而易见，添加 body
6. 检查是否有关联 Issue（通过 branch 名或 diff 中的注释推断）

## 输出格式

<type>(<scope>): <summary>

<空行>
<body: 1-3 句话解释 WHY>

<空行>
<footer: Closes #xxx 或 Refs #xxx>

## 示例

### 简单修复

输入：修改了一行代码，修复了时区相关的 Bug

输出：
fix(auth): correct token expiration timestamp comparison

JWT exp field uses seconds since epoch, but Date.now() returns
milliseconds. Multiplying by 1000 prevents premature token rejection.

### 新功能

输入：添加了多个文件，实现了用户导出功能

输出：
feat(export): add CSV export for user data

Users can now export their profile data as CSV from the settings page.
Includes all non-sensitive fields with proper UTF-8 encoding.

Closes #456

## 约束

- 标题行不超过 50 字符
- body 每行不超过 72 字符
- 不要在标题末尾加句号
- 使用祈使语气："add" 不是 "added"，"fix" 不是 "fixed"
- 如果改动涉及多个不相关的功能，建议用户拆分为多次提交
- 不要猜测 Issue 号——只在有明确证据时才添加 footer

## 质量标准

一个好的提交信息：
- 看了标题就知道改了什么（不需要看 diff）
- body 解释的是"为什么"而不是"做了什么"（diff 已经说明了"做了什么"）
- 三个月后回看能理解当时的决策背景
```

对比第一版的 20 行模糊版本，这个 Skill 有了：
- 明确的步骤（6 步）
- 精确的输出格式
- 具体的示例（2 个不同场景）
- 具体的约束（6 条限制）
- 质量标准（3 个判断维度）

## 3.5 一个指令要素过多不如不写

五个要素不意味着每个 Skill 都必须全部包含。过度工程化的指令和模糊指令一样有问题——它会让 Agent 迷失在细节中。

| Skill 复杂度 | 建议包含的要素 |
|-------------|--------------|
| 简单（10-30 行） | 步骤序列 + 约束 |
| 中等（30-100 行） | 步骤序列 + 输出格式 + 约束 |
| 复杂（100+ 行） | 全部五个要素 |

对于 `quick-fix` 这样的简单 Skill，不需要角色声明和质量标准——它的步骤本身就足够清晰。只有当任务复杂到 Agent 需要"判断力"时，才需要角色声明和质量标准。

## 3.6 避免的反模式

### 反模式 1: 解释 Agent 已知的知识

```markdown
# 坏
Python 是一种动态类型语言。在 Python 中，函数用 def 关键字定义。
列表用方括号 [] 表示。字典用花括号 {} 表示。
现在，请为以下函数生成单元测试...

# 好
为以下函数生成单元测试...
```

Agent 已经知道 Python 语法。不要浪费 tokens 教它基础知识。

### 反模式 2: 重述 Agent 的内置能力

```markdown
# 坏
你可以使用 Read 工具来读取文件。Read 工具接受一个文件路径参数，
返回文件的内容。你也可以使用 Edit 工具来修改文件...

# 好
1. 用 Read 读取目标文件
2. 用 Edit 修复问题
```

Agent 知道自己有什么工具和怎么用它们。只需要告诉它**在什么时候**用哪个工具。

### 反模式 3: 写散文而不是指令

```markdown
# 坏
代码审查是软件开发中非常重要的实践。通过代码审查，我们可以提前发现潜在的问题，
提升代码质量，促进团队知识共享。在进行代码审查时，我们应该关注多个方面，
包括但不限于代码的正确性、安全性、可读性和性能...

# 好
## 审查清单
1. **正确性**: 逻辑是否正确？边界条件是否处理？
2. **安全性**: 是否有注入、路径遍历、信息泄露？
3. **可读性**: 命名是否清晰？函数是否过长？
4. **性能**: 是否有 N+1 查询？不必要的循环？
```

Skill 不是论文，是操作手册。每个句子都应该是可执行的指令或必要的上下文。

### 反模式 4: 矛盾的指令

```markdown
# 坏
- 审查要全面，覆盖所有方面
- 审查要简洁，只关注关键问题
```

Agent 会困惑：到底是全面还是简洁？如果有优先级，明确说出来："优先检查安全和正确性。只在时间允许时检查代码风格。"

## 3.7 解释 Why，而非堆砌 MUST

在写了大量 Skill 之后，你可能会养成一个习惯：用大写的 ALWAYS 和 NEVER 来强调关键规则。但 Anthropic 从大规模 Skill 实践中提炼出一个反直觉的洞察：

> "Try hard to explain the **why** behind everything you're asking the model to do. Today's LLMs are *smart*. If you find yourself writing ALWAYS or NEVER in all caps, that's a yellow flag — reframe and explain the reasoning so that the model understands why the thing you're asking for is important."

简单说：**不要把 Skill 写成法条，要写成教程。**

### 法条式 vs 教程式

```markdown
# 法条式（坏）
ALWAYS use semicolons at the end of statements.
NEVER use tabs for indentation.
MUST include error handling in every function.
```

```markdown
# 教程式（好）
We use semicolons because our linter (ESLint) requires them,
and the CI pipeline rejects PRs without them.

Use spaces instead of tabs because our formatter (Prettier) is
configured for 2-space indentation — mixed tabs/spaces cause
diff noise in code review.

Include error handling because this service runs unattended in
production. Silent failures cause data inconsistency that's
hard to debug after the fact.
```

为什么教程式更好？因为今天的 LLM 有很强的推理能力和"心智理论"。当它理解了**原因**，它就能在未预见的场景中做出正确判断——比如遇到一个例外情况，法条式的 Agent 会机械执行（或者干脆忽略），而理解了原因的 Agent 会灵活应对。

### 什么时候 MUST 是合理的

并非所有场景都不能用强命令。安全边界和不可逆操作值得用 MUST：

```markdown
# 合理的 MUST
MUST confirm with user before running `DROP TABLE` or `rm -rf`.
```

判断标准：如果违反这条规则的后果是**不可逆的数据丢失或安全风险**，用 MUST。如果只是代码风格偏好，解释原因。

### 从 MUST 到 Why 的改写练习

| 改写前 (法条式) | 改写后 (教程式) |
|---------------|---------------|
| `ALWAYS write tests before implementation.` | `Write tests first because our test suite serves as the spec — it documents expected behavior before code exists.` |
| `NEVER modify files outside the src/ directory.` | `Only modify files in src/ — files outside it (config, CI, docs) are maintained by separate workflows and manual edits cause merge conflicts.` |
| `MUST use TypeScript strict mode.` | `Use TypeScript strict mode because it catches null-reference bugs at compile time that would otherwise reach production.` |

> **Tip**: 当你在 Skill 中写出 ALWAYS/NEVER 时，把它当作一个信号——暂停，问自己"为什么？"，然后把答案写进去。

## 3.8 指令语言的匠人规范

如果说"解释 Why"是 Skill 写作的**哲学**，那么指令语言规范就是**手艺**。以下是从大量优秀 Skill 中提炼的具体写作规则。

### 规则 1: 祈使句 > 陈述句

```markdown
# 祈使句（好）
Read the configuration file.
Run the test suite.
Report only high-severity issues.

# 陈述句（差）
You should read the configuration file.
The test suite needs to be run.
It would be good to focus on high-severity issues.
```

祈使句直接说"做什么"，陈述句在说"你应该做什么"——多了一层间接性，Agent 的执行力反而下降。

### 规则 2: 表格 > 列表 > 段落

信息密度和可解析性的排序：

```markdown
# 段落（差 — Agent 需要解析自然语言）
When the user says "scan" or "detect", use SCAN mode to run the
detector. When they say "review" or "fix", switch to REVIEW mode
for interactive fixing. When they say "auto" or "fix all", use
AUTO mode with guardrails enabled.

# 表格（好 — 结构清晰，一目了然）
| User Says              | Mode   | Action                    |
|------------------------|--------|---------------------------|
| "scan", "detect"       | SCAN   | Run detector, save state  |
| "review", "fix"        | REVIEW | Interactive fix session    |
| "auto", "fix all"      | AUTO   | Batch fix with guardrails |
```

### 规则 3: 代码示例 > 文字描述

```markdown
# 文字描述（差）
输出应该是 JSON 格式，包含一个 status 字段和一个 results 数组。

# 代码示例（好）
输出格式：
{
  "status": "success",
  "results": [
    {"file": "src/auth.ts", "issue": "missing null check", "severity": "high"}
  ]
}
```

### 规则 4: 正反对照 > 单一示例

人类通过对比学习，Agent 也一样。给一个"好的"和一个"坏的"，比给两个"好的"更有效：

```markdown
❌ `Added new feature` (past tense, capitalized)
✅ `feat: add new feature` (imperative, lowercase)
```

### 规则 5: 避免第二人称

```markdown
# 第二人称（避免）
You need to read the session history before analyzing.

# 祈使句（推荐）
Read the session history before analyzing.
```

"You need to" 不仅浪费 tokens，还可能让 Agent 把这理解为建议而非指令。

## 3.9 指令的长度控制

SKILL.md 正文的理想长度是 **100-300 行**（约 500-2000 tokens）。这个范围基于两个限制：

- **下限**：少于 100 行的 Skill 通常不值得做成 Skill（直接在对话中说就好了）
- **上限**：超过 500 行的 Skill 应该考虑三层架构（第 7 章），把非核心内容放到辅助文件中

如果你发现 SKILL.md 越写越长，问自己：

1. 有没有内容是在解释 Agent 已知的知识？→ 删
2. 有没有内容可以做成参考文档（reference/）？→ 移
3. 有没有内容可以做成脚本（scripts/）？→ 移
4. 有没有内容是给用户看的，不是给 Agent 看的？→ 删

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 指令写成散文，模糊抽象 | 用五要素写出结构化的可执行指令 |
| Agent 执行结果不可预测 | 输出格式和行为可预期 |
| 不知道指令应该多长 | 理解指令粒度和长度的选择 |
| 用 ALWAYS/NEVER 堆砌规则 | 解释 Why，让 Agent 理解原因后自主判断 |
| 不知道给 Agent 多少自由度 | 用窄桥/开阔地模型匹配任务类型 |

**Cumulative capability**: 你现在拥有 3 个 Skill（`quick-fix`、`code-review` v3、`commit-message`），并掌握了 description 写作和结构化指令写作两项核心技能。

## Try It Yourself

> 完整代码见 `code/track-1/ch03-commit-message/`，可直接复制到 `~/.qoder/skills/` 使用。
>
> **Track 2 演进**：对比 `code/track-2/v02-description/` 和 `code/track-2/v03-five-elements/` 的 diff，
> 观察五要素如何将 15 行骨架扩展为 38 行结构化指令。

1. **Verify**: 用改写后的 `commit-message` Skill 生成 5 条提交信息（对不同类型的改动：Bug 修复、新功能、重构、文档、配置变更）。每条都检查是否符合约束条件。

2. **Extend**: 回到第 1 章的 `quick-fix` Skill，用本章的五要素重写它的正文。对比改写前后 Agent 的行为差异。

3. **Explore**: 找一个你觉得 Agent 执行得"不够好"的任务。分析原因：是 description 问题（没加载）还是指令问题（加载了但执行不好）？如果是指令问题，用本章方法重写。

4. **Rewrite**: 找出你现有 Skill 中的 3 处 ALWAYS/NEVER/MUST，用"解释 Why"的方式改写。观察 Agent 行为是否改善。

## Summary

- 模糊的指令让 Agent 猜测，精确的指令让 Agent 执行
- 可执行指令有五个要素：**角色声明、步骤序列、输出格式、约束条件、判断标准**
- 根据**自由度匹配**选择指令精确度——窄桥型任务给精确命令，开阔地型任务给方向性指引
- **解释 Why 而非堆砌 MUST**——给 Agent 理由，它会比盲从指令做得更好
- 指令语言五规则：祈使句、表格优先、代码示例、正反对照、避免第二人称
- 避免四个反模式：解释已知知识、重述内置能力、写散文、矛盾指令
- SKILL.md 正文理想长度 100-300 行，过长考虑三层架构（第 7 章）
- 每个 Skill 不需要包含全部五个要素——根据复杂度选择

## Further Reading

- Conventional Commits 规范：conventionalcommits.org
- 《Prompt Engineering Guide》——指令设计的通用原则
- 第 6 章《模板与示例》——如何用示例进一步锚定 Agent 行为
- 第 9 章《质量检查清单》——如何让 Skill 自我验证输出质量
- Anthropic "Explain Why" 哲学——来自 Skill-Creator 的编写哲学
