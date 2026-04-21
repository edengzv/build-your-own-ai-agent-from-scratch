# Chapter 9: 质量检查清单

> **Motto**: "好的 Skill 自己知道自己做得好不好"

> 你已经掌握了 Skill 的所有核心技巧：description、指令、Multi-Pass、命令、模板、三层架构、工具编排。但还有一个关键缺失——Agent 怎么知道自己的输出合不合格？本章你将学会在 Skill 中内置 Quality Checklist，让 Agent 在输出前自检。

![Chapter 9: 质量检查清单](images/ch09-quality-checklist.png)

## The Problem

你的 `pr-reviewer` Skill 让 Agent 审查 Pull Request。大多数时候做得不错，但偶尔会：

- 遗漏了新增的文件（只看了修改的文件）
- 对测试文件发了和生产代码同等严格的审查意见
- 忘了检查 PR 描述是否完整
- 输出的格式和上次完全不一样

这些不是指令问题——指令足够清晰。问题是：Agent 没有一个"完成前检查"的步骤。它生成完就输出了，不会回头看看自己是否遗漏了什么。

## The Solution

**Quality Checklist** 是一组可验证的检查项，放在 Skill 正文的末尾（或作为最后一个 Pass），让 Agent 在输出前逐一核对。

```markdown
## Quality Checklist

完成输出前，逐项验证：

```
内容完整性：
- [ ] 所有新增文件都已审查
- [ ] 所有修改文件都已审查
- [ ] 删除的文件已确认合理性
- [ ] PR 描述已检查

审查质量：
- [ ] 每个问题都有具体的文件位置
- [ ] 每个问题都有改进建议
- [ ] 严重度标记合理（不是全 high 或全 low）
- [ ] 没有对测试文件应用生产代码标准

输出格式：
- [ ] 使用了规定的输出模板
- [ ] 问题按严重度排序
- [ ] 摘要部分简明扼要
```
```

## 9.1 为什么 Checklist 有效

Checklist 之所以有效，是因为它利用了 LLM 的一个特性：**当你明确要求它检查某件事时，它会认真检查**。

没有 Checklist 时，Agent 会"自然地"结束——生成到感觉差不多了就停。有了 Checklist，Agent 会在"感觉差不多"之后额外扫描一遍自己的输出：

```
Agent 的心理过程：
1. 生成审查报告...
2. 感觉差不多了...
3. 等等，让我看看 Checklist...
4. "所有新增文件都已审查"——我确实看了所有修改文件，
   但新增文件呢？让我检查... 哦，有 3 个新增文件我没看。
5. 补充审查新增文件...
6. 继续 Checklist...
```

这和飞行员的起飞前检查清单（preflight checklist）是同一个原理——不依赖记忆，依赖清单。

## 9.2 Checklist 设计原则

### 原则 1: 可验证

每个检查项必须是可以客观回答"是/否"的问题：

```markdown
# 好：可验证
- [ ] 标题行不超过 50 字符
- [ ] 所有文件都已检查

# 坏：不可验证
- [ ] 审查质量够高
- [ ] 建议有用
```

### 原则 2: 分类组织

按维度分组，而不是混在一起：

```markdown
# 好：分类清晰
内容完整性：
- [ ] ...
- [ ] ...

审查质量：
- [ ] ...
- [ ] ...

# 坏：混在一起
- [ ] 所有文件都检查了
- [ ] 格式正确
- [ ] 没遗漏文件
- [ ] 建议有具体位置
```

### 原则 3: 数量适中

```
5-8 项：简单 Skill
8-15 项：中等 Skill
15-20 项：复杂 Skill
20+ 项：太多了——拆分或精简
```

### 原则 4: 对应痛点

每个检查项应该对应一个**实际出过的问题**。不要为了凑数添加显而易见的检查项：

```markdown
# 坏：显而易见，没有价值
- [ ] 输出了内容（不为空）

# 好：对应实际痛点
- [ ] 没有对测试文件应用生产代码标准
```

## 9.3 完整的 pr-reviewer Skill

```markdown
---
name: pr-reviewer
description: 审查 Pull Request。检查代码变更的正确性、安全性、测试覆盖和 PR 描述质量。当用户需要 PR review 或 code review 时使用。
---

# PR Reviewer

对 Pull Request 进行全面审查，输出结构化的审查报告。

## Commands

| Command | Purpose |
|---------|---------|
| `/pr-reviewer review` | 审查当前分支的 PR 改动 |
| `/pr-reviewer review <file>` | 只审查指定文件 |
| `/pr-reviewer summary` | 生成 PR 描述草稿 |

## `/pr-reviewer review`

### 执行步骤

1. **[Bash]** 运行 `git diff main...HEAD --stat` 查看改动文件列表
2. **[Bash]** 运行 `git diff main...HEAD` 查看完整 diff
3. 按以下清单审查每个文件：

### 审查清单

对每个文件检查：

**正确性**
- 逻辑是否正确？变量/状态的流转是否合理？
- 边界条件是否处理？（空值、零值、溢出）
- 并发安全吗？（如果涉及共享状态）

**安全性**
- 是否有注入风险？（SQL、命令、XSS）
- 敏感数据是否正确处理？（密码、token、PII）
- 权限检查是否完整？

**测试影响**
- 改动是否有对应的测试？
- 已有测试是否需要更新？

**设计**
- 改动是否符合项目的现有模式？
- 是否有更简单的实现方式？

### 输出格式

对每个发现的问题：

```
### [severity: high/medium/low] - <one-line summary>
**文件**: `<path>` (L<start>-L<end>)
**问题**: <详细描述>
**建议**: <具体的改进方案>
```

最终输出一个摘要：

```
## 审查摘要

- **文件数**: N 个文件 (+M 新增, -K 删除)
- **问题数**: X high, Y medium, Z low
- **总评**: <一句话总体评价>
- **建议**: <是否可以合并的建议>
```

## Quality Checklist

完成审查后，逐项验证：

```
内容完整性：
- [ ] 所有新增文件（git diff --stat 中标记 A 的）都已审查
- [ ] 所有修改文件都已审查
- [ ] 大文件（>200 行改动）给予了更多关注
- [ ] 如果有删除文件，确认删除是否合理

审查质量：
- [ ] 每个问题都有具体的文件和行号
- [ ] 每个问题都有可操作的改进建议
- [ ] 严重度分布合理（不是全 high）
- [ ] 没有对测试文件应用生产代码的严格标准
- [ ] 正面反馈也有提及（好的设计、清晰的代码）

输出格式：
- [ ] 使用了规定的问题模板
- [ ] 摘要包含文件数、问题数、总评
- [ ] 问题按严重度排序（high → medium → low）
```

如果有任何一项未通过，修正后再输出最终结果。
```

## 9.4 案例：真实 Skill 中的 Checklist 设计

### wechat-article-writer (16 项)

```
内容质量：
- [ ] 标题 30 字以内，有吸引力，不标题党
- [ ] 开头 60 字可独立作为预览，引发好奇心
- [ ] 正文 2000-4000 中文字符
- [ ] 是原创分析，不是翻译或洗稿
- [ ] 技术准确性已验证
- [ ] 代码示例不超过 15 行

视觉质量：
- [ ] 封面图比例 2.35:1
- [ ] 内文配图 1080px 宽
- [ ] 图文搭配协调

微信适配：
- [ ] 仅使用微信兼容 Markdown
- [ ] 结尾有互动引导
- [ ] 来源标注完整

写作风格：
- [ ] 第二人称"你"贯穿全文
- [ ] 无套话
- [ ] 无过度修饰
- [ ] 段落 3-5 句
```

注意每一项都是**可验证的**——"标题 30 字以内"可以数，"2000-4000 字"可以量，"不标题党"虽然主观但有具体的反面案例作为参照。

### tech-book-writer (20+ 项)

分为 4 大类——技术质量、渐进结构、写作风格、完整性——每类 5-7 项。这是本书见过的最完整的 Checklist 设计，因为书籍写作的质量维度最多。

### 共同模式

横向对比这些 Checklist，我发现 3 个共同模式：

1. **数字约束占多数**：字数限制、数量限制、比例限制——这些是最容易验证的
2. **平台约束单独一类**：微信、抖音等平台有各自的限制，值得独立检查
3. **"否定式"检查项很有效**："没有标题党"、"没有过度修饰"——告诉 Agent 什么不该出现

## 9.5 Checklist 的位置

Checklist 放在 SKILL.md 的什么位置？两种策略：

### 策略 1: 放在末尾（推荐）

```markdown
## 执行步骤
...

## Quality Checklist
...
```

Agent 自然地在完成步骤后看到 Checklist，作为"完成前的最后一关"。

### 策略 2: 作为 Multi-Pass 的最后一步

```markdown
### Pass 3 — 质量验证

对 Pass 2 的输出进行自检：
[checklist]

如果有不合格项，回到 Pass 2 修正。最多修正 2 次。
```

这种方式更强制——把 Checklist 变成了工作流的一部分，而不仅仅是"建议检查"。

## 9.6 Guardrails：告诉 Agent 什么不该做

Checklist 告诉 Agent "做完后检查这些"。但还有一个同等重要的维度：**提前告诉 Agent 什么不该做**。

这就是 Guardrails（护栏）设计模式。如果 Checklist 是"终点的质量门"，Guardrails 就是"沿途的防护栏"。

### 为什么需要 Guardrails

Agent 在执行复杂任务时有一些常见的"自由发挥"倾向：

- 修复一个 Bug 时顺手重构了周边代码
- 删除了它认为"不需要"的错误处理代码
- 用更"简洁"的写法替换了项目既有的编码风格
- 在高风险操作中没有确认就直接执行

这些行为单独看可能"合理"，但在真实项目中会引发问题。Guardrails 的作用是在 Skill 中预先标明这些禁区。

### Guardrails 模板

```markdown
## Guardrails

- Do not remove protections at trust boundaries (user input validation,
  auth checks, network sanitization, database constraints).
- Do not replace real typing with weaker typing (e.g., any, unknown).
- Prefer minimal edits over broad rewrites — touch only what's needed.
- Keep project conventions even if you know a "better" way.
- Do not run destructive commands (DROP TABLE, rm -rf, force push)
  without explicit user confirmation.
```

### Anti-Patterns 部分

Guardrails 的补充是 **Anti-Patterns 清单**——列出 Agent 在这个 Skill 场景中最容易犯的具体错误：

```markdown
## Anti-Patterns (Don't Do These)

- Don't summarize every session — only extract *lessons*
- Don't read full JSONL files — tail/limit only
- Don't write vague insights ("improve response quality")
- Don't duplicate existing knowledge in the file
- Don't create new files when appending to existing ones works
```

注意 Anti-Patterns 比 Guardrails 更具体——它们是针对**这个 Skill 的特定场景**的常见失误。Guardrails 是通用的安全边界，Anti-Patterns 是场景化的经验教训。

### 高权限 Skill 的安全模型

对于能执行 shell 命令、访问网络或操作文件系统的 Skill，需要在最开头声明安全模型：

```markdown
## Security & Privilege Model

> This is a high-privilege skill. Read before using.

**Spawned workers inherit full host-agent runtime**, including:
- exec (arbitrary shell commands)
- All installed skills
- sessions_spawn (workers can spawn sub-agents)

**Batch mode removes all human gates.** Only use for tasks
and environments you fully trust.
```

### 破坏性操作标记

在 Skill 中遇到不可逆的命令时，用明显的标记：

```markdown
git reset --hard HEAD~3     # destructive — loses uncommitted changes
docker system prune -a -f   # destructive — removes ALL unused Docker data
```

### 何时需要 Guardrails

| Skill 类型 | Guardrails 需求 |
|-----------|----------------|
| 只读类（审查、分析、报告） | 基本的：不修改文件、不执行命令 |
| 编辑类（修复、重构、生成） | 中等的：不扩大修改范围、保持项目风格 |
| 操作类（部署、迁移、清理） | 必须的：安全模型声明 + 破坏性操作标记 + 确认门控 |

> **Tip**: 一个好的经验法则——如果你的 Skill 有 `Bash` 工具权限，它就需要 Guardrails。

## 9.7 打破确认偏误：生成器-验证器隔离

Checklist 让 Agent 自检。但这里有一个微妙的问题：**让创作者检查自己的作品，存在确认偏误（confirmation bias）**。

Agent 生成了一段代码，然后自己去检查这段代码——它倾向于认为自己的输出是正确的。这和人类作者校对自己文章时总是发现不了错别字是同一个心理机制。

### EvoSkills 的发现

学术项目 EvoSkills 在 Skill 自动优化实验中发现：当同一个 Agent 既创建 Skill 又测试 Skill 时，通过率只有 32%。但当他们引入**独立的验证 Agent**——一个没有参与创建过程的"新鲜"Agent 来测试——通过率提升到了 75%。

原因很简单：新鲜的 Agent 没有创建过程中的上下文和假设，它会从用户的视角审视 Skill 的输出，而不是从创作者的视角。

### 实践建议

你不需要真的部署两个 Agent。以下是实用的隔离策略：

**策略 1: 换一个对话窗口测试**

创建 Skill 的过程在对话 A 中进行。测试时，打开一个全新的对话 B（不带之前的上下文），加载 Skill 并执行测试用例。这样测试 Agent 就是"新鲜"的——它不知道你在创建时做了什么假设。

**策略 2: 让同事用你的 Skill**

最好的验证者是另一个人。他们会用你没想到的方式描述任务，会遇到你没考虑的边界情况。

**策略 3: 在 Skill 中分离 Worker 和 Judge**

回忆第 4 章的循环反馈模式——Worker/Judge 架构本质上就是在同一个 Skill 内实现生成器-验证器隔离。Judge 的指令应该明确要求它从**批判**视角评估，而不是从"帮 Worker 通过检查"的视角。

### 与 Checklist 的关系

Checklist、Guardrails、Generator-Verifier 隔离是质量保证的三个层次：

```
Level 1: Checklist    — 完成后自检（发现遗漏）
Level 2: Guardrails   — 执行中约束（防止越界）
Level 3: 隔离验证      — 独立视角评估（打破偏见）
```

大多数 Skill 只需要 Level 1。高风险 Skill 需要 Level 1 + 2。极高质量要求的 Skill（如面向生产的代码生成、公开发布的内容）值得 Level 1 + 2 + 3。

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 输出质量靠运气 | Checklist 确保一致性 |
| Agent 生成完就输出 | 输出前逐项自检 |
| 没有质量标准 | 可验证的检查项 |
| 不知道怎么限制 Agent 的"自由发挥" | 用 Guardrails 设定禁区，用 Anti-Patterns 标记常见失误 |
| 让 Agent 自己检查自己的输出 | 理解确认偏误，掌握生成器-验证器隔离策略 |

**Cumulative capability**: 你的 Skill 不仅有 Checklist（自检），还有 Guardrails（约束）和隔离验证策略（打破偏见）。三层质量保证体系完整。

## Try It Yourself

> 完整代码见 `code/track-1/ch09-pr-reviewer/`，可直接复制到 `~/.qoder/skills/` 使用。
>
> **Track 2 演进**：对比 `code/track-2/v08-tools/` 和 `code/track-2/v09-quality/` 的 diff，
> 观察 Guardrails、10 项清单和反模式检查如何从 307 行扩展到 321 行。

1. **Verify**: 用 `pr-reviewer` 审查一个真实的 PR（或创建一个测试 PR）。检查 Agent 是否在输出前执行了 Checklist。
2. **Extend**: 给 Chapter 6 的 `test-writer` 添加 8 项 Quality Checklist（覆盖测试覆盖度、断言质量、命名规范等）。
3. **Explore**: 审查你所有 Skill 的输出记录，找出 3 个最常出现的质量问题。为每个问题设计一个 Checklist 项。
4. **Guardrails**: 为你的 `code-review` Skill 添加 Guardrails 部分——列出 Agent 在审查时不应该做的 5 件事。
5. **Isolation**: 在一个新的对话窗口中（不带之前的上下文）测试你的 `commit-message` Skill。对比同一对话中测试和新对话中测试的结果差异。

## Summary

- **Quality Checklist** 让 Agent 在输出前逐项自检
- Checklist 有效的原因：LLM 被明确要求检查时会认真执行
- 设计原则：**可验证**、**分类组织**、**数量适中**（5-20 项）、**对应实际痛点**
- **Guardrails** 设定执行禁区——告诉 Agent 什么不该做，比告诉它该做什么更重要
- **Anti-Patterns** 是场景化的常见失误清单，比 Guardrails 更具体
- 高权限 Skill 必须声明安全模型，破坏性操作必须标记
- **确认偏误**：让创作者检查自己的作品会遗漏问题——用独立视角验证
- 三层质量保证：Checklist（自检）→ Guardrails（约束）→ 隔离验证（打破偏见）

## Further Reading

- Atul Gawande 《清单革命》(The Checklist Manifesto)：Checklist 在医疗和航空领域的应用
- 第 10 章《测试与调优》——Checklist 不够时，如何通过系统性测试提升质量
- 第 11 章《案例解剖》——深入分析优秀 Skill 的 Checklist 和 Guardrails 设计
- EvoSkills (Zhao et al.) — 生成器-验证器隔离的学术验证
