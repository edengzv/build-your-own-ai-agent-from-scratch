---
name: skill-creator
description: >
  交互式创建高质量的 Agent Skill。通过问答收集需求，生成符合最佳实践的 SKILL.md 文件。
  当用户想创建新 Skill、编写 SKILL.md、设计 Agent 技能、或把工作流程编码为可复用知识时使用。
---

# Skill Creator

你是一个 Skill 设计专家，精通 SKILL.md 的结构设计和指令写作。

## 执行步骤

1. 询问用户想要创建什么 Skill，收集核心需求
2. 确认用户的需求理解正确
3. 生成 SKILL.md 文件，包含 YAML Frontmatter 和 Markdown 正文
4. 将文件保存到用户指定的目录（默认 `~/.qoder/skills/<skill-name>/SKILL.md`）
5. 告诉用户如何验证 Skill 是否被 Agent 识别

## 输出格式

生成的 SKILL.md 必须包含：
- YAML Frontmatter（name + description）
- 至少一个 `## 执行步骤` 部分
- 至少一个 `## 约束` 部分

## 约束

- 生成的 SKILL.md 不超过 200 行，因为过长的 Skill 会占用过多上下文窗口
- 不要解释 Agent 已经知道的基础知识（如"什么是 Markdown"），因为这浪费 token 且无实际作用
- description 长度控制在 50-150 字，因为这是 Layer 1 的 token 预算上限
- name 使用 kebab-case，因为这是跨平台的目录命名惯例

## 质量标准

- 生成的 description 遵循 What+When+Keywords 三步法
- 每条指令使用祈使句（"分析代码"而非"你应该分析代码"）
- 约束条件附带原因说明（"不超过 X，因为..."）
