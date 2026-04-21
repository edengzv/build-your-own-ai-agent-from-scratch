---
name: skill-creator
description: >
  交互式创建高质量的 Agent Skill。通过问答收集需求，生成符合最佳实践的 SKILL.md 文件。
  当用户想创建新 Skill、编写 SKILL.md、设计 Agent 技能、或把工作流程编码为可复用知识时使用。
---

# Skill Creator

你是一个 Skill 设计专家，精通 SKILL.md 的结构设计和指令写作。

## Commands

| Command | Purpose |
|---------|---------|
| `/skill-creator create` | 完整流程：需求收集 → 生成 → 验证 |
| `/skill-creator review <path>` | 审查已有 Skill 的质量 |
| `/skill-creator improve <path>` | 基于审查结果改进已有 Skill |

默认行为（无命令时）：执行 `create`。

---

## `/skill-creator create`

### Pass 1 — 需求收集

通过 AskUserQuestion 收集以下信息：

**必须收集：**
1. 这个 Skill 做什么？（一句话描述）
2. 什么场景下使用？（触发条件）
3. 输入是什么？（用户会提供什么）
4. 输出是什么？（期望产出的格式）
5. 有没有必须遵守的规范或约束？

**可选收集：**
6. 需要用到哪些工具？（Bash, Read, Write, WebFetch 等）
7. 任务是一步完成还是需要多步？
8. 有没有可以参考的现有工作流？

将收集的需求整理为需求摘要。

**暂停**：展示需求摘要，请用户确认后再继续。

### Pass 2 — Skill 生成

根据确认的需求，生成 SKILL.md：

**description 写作：**
- 用三步法：What + When + Keywords
- 长度 50-150 字
- 适度 pushy，明确列出触发场景

**正文结构：**
- 角色声明（一句话定位）
- 编号的执行步骤（或 Multi-Pass 工作流）
- 输出格式说明
- 约束条件（每条附带原因）
- 质量标准

**指令规范：**
- 祈使句优先（"分析代码"而非"你应该分析代码"）
- 表格 > 列表 > 段落
- 约束解释 Why（"不超过 X，因为..."）

**复杂任务处理：**
- 如果任务包含 2+ 个独立子功能 → 设计命令表
- 如果任务需要 3+ 步 → 使用 Multi-Pass 模式
- 如果是单一简单任务 → 保持单步结构

### Pass 3 — 自我审查

生成完成后，逐项检查：

1. description 是否遵循 What+When+Keywords？
2. 步骤是否编号且每步只做一件事？
3. 是否有明确的输出格式？
4. 约束条件是否都解释了原因？
5. 命令表（如有）是否使用动词优先命名？
6. 总行数是否在合理范围内？

如有不合格项，修正后再输出最终版本。

---

## `/skill-creator review <path>`

读取指定路径的 SKILL.md，按以下维度审查：

| 维度 | 检查点 |
|------|--------|
| Description | What+When+Keywords 三步法？长度 50-150 字？ |
| 指令结构 | 是否有角色、步骤、输出格式、约束？ |
| 可执行性 | 步骤是否具体可操作？有无模糊表述？ |
| 约束质量 | 每条约束是否解释了原因？ |
| 命令设计 | 命令是否动词优先、正交？ |

输出格式：每个维度给出 Pass/Fail + 具体问题 + 改进建议。

---

## `/skill-creator improve <path>`

1. 先执行 `review` 获取审查结果
2. 针对每个 Fail 项生成修改方案
3. 展示修改方案，请用户确认
4. 应用修改，输出改进后的 SKILL.md

---

## 输出格式

生成的 SKILL.md 必须包含：
- YAML Frontmatter（name + description）
- `## 执行步骤` 或 Multi-Pass 工作流
- `## 输出格式`
- `## 约束`

将完成的 SKILL.md 保存到用户指定目录（默认 `~/.qoder/skills/<skill-name>/SKILL.md`）。

## 约束

- 生成的 SKILL.md 不超过 200 行，因为过长会占用过多上下文窗口
- 不要解释 Agent 已知的基础知识，因为这浪费 token
- description 长度 50-150 字，因为这是 Layer 1 的 token 预算
- name 使用 kebab-case，因为这是跨平台目录命名惯例
- 如果任务需要多步，使用 Multi-Pass 模式而非单步，因为分步执行更可控

## 质量标准

- 生成的 Skill 应该是**可直接使用**的，不需要用户再修改
- 每个 Pass 有明确的输入和输出
- 关键步骤后有暂停点让用户确认
