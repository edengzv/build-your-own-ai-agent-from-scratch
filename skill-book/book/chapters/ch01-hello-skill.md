# Chapter 1: 你好，Skill

> **Motto**: "一个 SKILL.md 文件就是全部的开始"

> 你已经用过 AI 编程工具——Claude Code、Cursor、Qoder。你知道它们能读文件、写代码、跑命令。但每次你让 Agent 做同样的事——"按我们团队规范审查代码"、"用这个模板写提交信息"——你都得重新描述一遍。本章你将写出第一个 Skill，让 Agent 永远记住你的工作流程。

![Chapter 1: 你好，Skill](images/ch01-hello-skill.png)

## The Problem

你在用 AI 编程工具做代码审查。第一次，你花了 5 分钟描述你的审查标准：

```
帮我审查这段代码。注意以下几点：
1. 检查是否有安全漏洞（SQL 注入、XSS、路径遍历）
2. 检查错误处理是否完善
3. 检查命名是否符合我们的规范（camelCase）
4. 每个问题用这个格式输出：
   [severity: high/medium/low]
   文件: xxx
   问题: xxx
   建议: xxx
```

Agent 做得不错。

第二天，你又需要审查代码。你又输入了类似的内容——但这次你漏掉了"安全漏洞"那一条，因为你记不清昨天写了什么。Agent 自然也就没检查安全问题。

第三天，你的同事也想用同样的标准。你把昨天的 Prompt 发给他——但他觉得格式不够好，自己改了一版。现在团队里有两套不同的审查标准。

这就是**知识没有持久化**的问题。你的审查标准存在聊天记录里，分散、不一致、不可复用。

我们需要一种方式，把这些"专家知识"从对话中提取出来，变成一个 Agent 随时可以加载的文件。这就是 **Skill**。

## The Solution

**Skill** 是一个文件夹，核心是一个 `SKILL.md` 文件。它用结构化的格式，告诉 Agent "当你需要做某件事时，按照这些指令来"。

```
~/.qoder/skills/          ← Skill 存放目录（Claude Code 为 ~/.claude/skills/）
└── code-review/          ← 一个 Skill = 一个文件夹
    └── SKILL.md          ← 核心文件：指令 + 元数据
```

Agent 启动时会扫描这个目录，读取每个 Skill 的**名称和简介**（大约 100 tokens），注入到自己的上下文中。当用户的请求匹配某个 Skill 的描述时，Agent 会主动加载该 Skill 的完整内容，然后按照指令执行。

这个过程完全自动——你不需要手动告诉 Agent "请加载 code-review 技能"。Agent 自己判断。

```
┌─────────────────────────────────────────┐
│             Agent 上下文                 │
│                                         │
│  System Prompt + 工具列表               │
│                                         │
│  可用 Skills:                           │
│   • code-review: 审查代码质量...        │  ← Layer 1: 只有名字和简介
│   • commit-msg: 生成提交信息...         │     (~100 tokens/skill)
│                                         │
└────────────────┬────────────────────────┘
                 │
                 │ 用户: "帮我审查 app.py"
                 │ Agent 判断: 这需要 code-review
                 ↓
        ┌──────────────┐
        │  加载 Skill   │  ← Layer 2: 读取完整内容
        └──────┬───────┘     (~2000 tokens)
               ↓
    ┌────────────────────────┐
    │  code-review/          │
    │    SKILL.md 完整内容    │
    │    审查清单、输出格式... │
    └────────────────────────┘
```

这就是 Skill 系统的核心设计：**两层注入，按需加载**。Layer 1 永远在线但极轻量，Layer 2 只在需要时才加载。Agent 自己决定何时需要什么知识。

## 1.1 SKILL.md 的最小结构

一个 SKILL.md 文件由两部分组成：

```markdown
---
name: quick-fix
description: 快速修复代码中的小 Bug。当用户报告一个简单的 Bug 或错误时使用。
---

# Quick Fix

当用户报告一个 Bug 时，按以下步骤操作：

1. 用 Read 工具读取相关代码文件
2. 定位 Bug 的根因
3. 用 Edit 工具修复 Bug
4. 解释你做了什么修改以及为什么
```

**YAML Frontmatter**（两行 `---` 之间的部分）是给机器读的元数据：

- `name`: Skill 的唯一标识符。小写字母、数字、连字符。
- `description`: Skill 的简介。这是 Agent 在 Layer 1 唯一能看到的信息——它决定了 Agent 是否加载这个 Skill。我们会在第 2 章深入讨论 description 的重要性。

**Markdown Body**（frontmatter 之后的部分）是给 Agent 读的指令。当 Skill 被加载（Layer 2），Agent 会读到这些内容并按照执行。

就这么简单。10 行，一个文件，一个文件夹。

> **Note**: YAML Frontmatter 是 Markdown 文件开头的元数据块，被广泛用于静态站点生成器（Jekyll, Hugo）和文档系统。如果你不熟悉，只需要记住：两行 `---` 之间写 `key: value` 对。

## 1.2 Skill vs 其他知识注入方式

在 AI 编程工具的生态中，有多种方式给 Agent 注入知识。理解它们的区别，才能知道什么时候该用 Skill：

| 方式 | 持久性 | 加载时机 | 适用场景 |
|------|--------|---------|---------|
| **对话 Prompt** | 本次对话 | 手动每次输入 | 一次性指令 |
| **System Prompt** | 每次对话自动 | 启动时全部加载 | 全局规则（如编码规范） |
| **CLAUDE.md / AGENTS.md** | 项目级持久 | 进入目录时自动加载 | 项目特定的规则和上下文 |
| **Skill** | 永久持久 | Agent 按需加载 | 可复用的程序化知识 |
| **MCP Server** | 永久持久 | 按需调用 | 外部数据源和 API |

Skill 的独特定位是：**可复用、跨项目、按需加载的程序化知识**。

- 不像 System Prompt 那样每次都占满上下文——Skill 只在需要时加载。
- 不像 CLAUDE.md 绑定在特定项目——Skill 是全局的，任何项目都能用。
- 不像 MCP Server 需要运行一个服务——Skill 只是一个 Markdown 文件。

把它想象成一本工具书的书架。System Prompt 是你桌上一直打开的那本；CLAUDE.md 是当前项目的说明书；Skill 是书架上的工具书——你知道它们在那里，需要时拿下来翻一翻。

## 1.3 创建你的第一个 Skill

让我们动手创建 `quick-fix` Skill。

**Step 1: 创建目录**

根据你使用的工具，Skill 的存放位置不同：

```bash
# Qoder
mkdir -p ~/.qoder/skills/quick-fix

# Claude Code
mkdir -p ~/.claude/skills/quick-fix
```

**Step 2: 写入 SKILL.md**

在 `quick-fix/` 目录下创建 `SKILL.md` 文件：

```markdown
---
name: quick-fix
description: 快速修复代码中的小 Bug。当用户报告一个简单的 Bug、错误、或 typo 时使用。
---

# Quick Fix

当用户报告一个 Bug 或错误时，按以下步骤操作：

1. 先确认 Bug 的表现：用户看到了什么错误？期望的行为是什么？
2. 用 Read 工具读取相关代码文件
3. 定位 Bug 的根因——不要只修表面症状
4. 用 Edit 工具做最小修改来修复 Bug
5. 解释你做了什么修改以及为什么这样修

## 约束

- 只修复用户报告的 Bug，不要顺便重构其他代码
- 如果修复涉及多个文件，逐一说明每个文件的改动
- 如果 Bug 的根因不明确，先询问用户更多信息，不要猜测
```

**Step 3: 验证**

重启你的 AI 编程工具（大多数工具需要重启才能扫描新 Skill），然后输入：

```
帮我修一下 app.py 里第 42 行的空指针错误
```

观察 Agent 的行为。如果一切正常，Agent 应该会：

1. 识别到这是一个 Bug 修复请求
2. 匹配到 `quick-fix` Skill 的 description
3. 加载 Skill 的完整指令
4. 按照步骤执行：确认问题 → 读代码 → 定位根因 → 修复 → 解释

> **Tip**: 如果 Agent 没有加载你的 Skill，检查两件事：(1) 文件路径是否正确；(2) YAML Frontmatter 格式是否正确（注意 `---` 后面不能有多余的空格）。

## 1.4 Skill 的生命周期

理解 Skill 从"躺在磁盘上"到"被 Agent 使用"的完整过程，能帮助你更好地设计 Skill。

### 阶段 1: 扫描（启动时）

Agent 启动时，扫描 Skills 目录。对每个 Skill，它只读取 YAML Frontmatter 中的 `name` 和 `description`，不读正文。

```python
# 伪代码：Agent 扫描 Skills
for folder in skills_directory:
    skill_md = folder / "SKILL.md"
    meta = parse_frontmatter(skill_md)  # 只读 name + description
    available_skills.append({
        "name": meta["name"],
        "description": meta["description"][:100],  # 截断到 100 字
        "path": skill_md,
    })
```

扫描结果被拼接到 Agent 的上下文中：

```
可用技能:
  - quick-fix: 快速修复代码中的小 Bug。当用户报告一个简单的 Bug、错误、或 typo 时使用。
  - code-review: 审查代码质量，检查安全、性能、可读性问题...
```

每个 Skill 在这里只占约 **100 tokens**。即使你有 20 个 Skill，也只多占约 2000 tokens——对于 200K token 上下文窗口来说微不足道。

### 阶段 2: 匹配（用户请求时）

当用户发送消息，Agent 会在处理请求前，根据 Layer 1 的摘要判断：这个请求需要加载哪个 Skill 吗？

这个判断完全由 LLM 完成——不是关键词匹配，而是语义理解。所以 description 的写法至关重要：它不需要包含用户会说的每一个词，但需要准确描述 Skill 的用途，让 LLM 能正确联想。

### 阶段 3: 加载（按需）

如果 Agent 决定需要某个 Skill，它调用 `load_skill` 工具，读取完整的 SKILL.md 正文（去掉 Frontmatter）。完整内容作为 tool result 进入对话历史。

```
[Skill: quick-fix]
# Quick Fix
当用户报告一个 Bug 或错误时，按以下步骤操作：
1. 先确认 Bug 的表现...
...
```

加载后，Agent 就有了完整的指令，可以按步骤执行了。

### 阶段 4: 执行

Agent 按照 Skill 正文中的指令，结合用户的具体请求，开始工作。在执行过程中，Skill 的指令相当于临时的"行为准则"——Agent 会尽量遵循，但也会根据实际情况做判断。

> **Important**: Skill 不是硬编码的程序。Agent 不会盲目执行每一步——它理解指令的意图，并根据上下文灵活应用。这是 Skill 和脚本的根本区别：Skill 指导的是一个有判断力的 Agent，而脚本控制的是一个无判断力的机器。

## 1.5 你的 Skill 工具箱

从本章开始，你将在整本书中逐步构建一个 **Skill 工具箱**。每一章你都会写出一个新的 Skill（或改进一个已有的 Skill），到最后你会拥有一整套自己设计的、经过验证的 Skill。

我建议在你的电脑上创建一个专门的目录来跟随本书实践：

```bash
mkdir -p ~/skill-workshop/skills
```

每章的产出都放在这个目录下。你可以用 Git 管理版本，这样可以追踪每个 Skill 的演进过程——从第 2 章的 `code-review` v1 到第 9 章的 v3，你会看到同一个 Skill 如何随着你的技巧提升而不断进化。

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 每次重新描述需求 | Skill 文件持久化知识 |
| 知识散落在聊天记录里 | 结构化存储在 SKILL.md 中 |
| 不了解 Skill 是什么 | 理解 Skill 的结构和生命周期 |

**Cumulative capability**: 你理解了 Skill 的核心概念，创建了第一个 `quick-fix` Skill，并亲眼看到 Agent 自动发现和加载它。

## Try It Yourself

> 完整代码见 `code/track-1/ch01-quick-fix/`，可直接复制到 `~/.qoder/skills/` 使用。
>
> **Track 2 演进**：查看 `code/track-2/v01-basic/SKILL.md`——这是 skill-creator 的起点，
> 仅 13 行的极简骨架。

1. **Verify**: 创建 `quick-fix` Skill，然后向 Agent 报告一个小 Bug（比如一个变量名拼错），观察 Agent 是否按照 Skill 的步骤执行。

2. **Extend**: 故意把 SKILL.md 的 Frontmatter 格式写错（比如少一行 `---`），看 Agent 还能不能识别到这个 Skill。然后修复它。

3. **Explore**: 列出你日常工作中最常对 AI 重复的 3 件事。哪些适合做成 Skill？哪些更适合写进 CLAUDE.md / AGENTS.md？用本章学到的对比表做判断。

## Summary

- **Skill** 是 Agent 的可复用知识包，核心是一个 `SKILL.md` 文件
- SKILL.md 由 **YAML Frontmatter**（name + description）和 **Markdown Body**（指令正文）组成
- Skill 采用**两层注入**：Layer 1 轻量摘要（~100 tokens）常驻上下文，Layer 2 完整内容按需加载
- Agent **自主决定**何时加载哪个 Skill——不需要用户手动触发
- Skill 的最小可行结构只需要 **10 行**——不要被复杂性吓住
- Skill 和 System Prompt / CLAUDE.md / MCP 各有定位，Skill 的独特价值是**跨项目、可复用、按需加载**

## Further Reading

- Anthropic 官方文档：Skill Authoring Best Practices
- skill-of-skills 目录 (https://github.com/the911fund/skill-of-skills)：686+ 社区 Skill 合集
- awesome-claude-skills (https://github.com/travisvn/awesome-claude-skills)：精选 Skill 列表
- 本书第 5 章《知识加载》（如果你读过《智能体入门》）：Skill 系统的底层实现原理
