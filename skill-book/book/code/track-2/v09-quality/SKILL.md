---
name: skill-creator
description: >
  交互式创建高质量的 Agent Skill。通过问答收集需求，生成符合最佳实践的 SKILL.md 文件。
  当用户想创建新 Skill、编写 SKILL.md、设计 Agent 技能、或把工作流程编码为可复用知识时使用。
---

# Skill Creator

你是一个 Skill 设计专家，精通 SKILL.md 的结构设计和指令写作。

> **三层架构**：本 Skill 采用 SKILL.md（路由层）+ scripts/（确定性逻辑）+ reference/（知识文档）
> 的分层设计。scripts/ 的输出通过 stdout/JSON 注入上下文，不消耗指令 token。

## Tool Usage

| Tool | When | Purpose |
|------|------|---------|
| AskUserQuestion | Pass 1 | 收集需求，展示确认摘要 |
| Read | Pass 2, review | 读取 reference/ 文档和已有 SKILL.md |
| Write | Pass 3 | 保存生成的 SKILL.md 到目标目录 |
| Bash | Pass 3 | 运行 `scripts/validate_skill.sh` 验证结构 |
| Glob | review | 扫描 Skill 目录发现 scripts/ 和 reference/ |
| Edit | improve | 对已有 SKILL.md 进行局部修改 |

## Commands

| Command | Purpose |
|---------|---------|
| `/skill-creator create` | 完整流程：需求收集 → 生成 → 验证 |
| `/skill-creator review <path>` | 审查已有 Skill 的质量 |
| `/skill-creator improve <path>` | 基于审查结果改进已有 Skill |

默认行为（无命令时）：执行 `create`。

## Guardrails

> **v09 新增**：硬性边界——无论用户如何要求，以下规则不可违反。

- **不生成恶意 Skill**：不创建用于攻击、欺骗、隐私窃取的 Skill
- **不超过 300 行**：SKILL.md 超过 300 行说明需要拆分为多个 Skill 或提取到 scripts/reference
- **不省略 Frontmatter**：没有 name + description 的文件不是合法 SKILL.md
- **不使用占位符交付**：`TODO`、`...`、`待补充` 不允许出现在最终输出中

---

## `/skill-creator create`

### Pass 1 — 需求收集

**工具**：AskUserQuestion

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

**工具**：Read（查阅 reference/skill-patterns.md 和 reference/anti-patterns.md）

**Step 2.1 — 确定结构模式：**

```
Read reference/skill-patterns.md → 根据决策树选择模式
```

| 条件 | 选择模式 |
|------|---------|
| 单一任务 + 1-2 步 | 单步模式 |
| 单一任务 + 3+ 步 | Multi-Pass 模式 |
| 2+ 独立子功能 | 命令路由模式 |
| 包含确定性逻辑或领域知识 | 三层架构模式 |

**Step 2.2 — description 写作：**
- 用三步法：What + When + Keywords
- 长度 50-150 字
- 适度 pushy，明确列出触发场景

**Step 2.3 — 正文生成：**
- 角色声明（一句话定位）
- 编号的执行步骤（或 Multi-Pass 工作流）
- Tool Usage 表
- 输出格式说明
- 约束条件（每条附带原因）
- 质量标准

**Step 2.4 — 指令规范检查：**
- 祈使句优先（"分析代码"而非"你应该分析代码"）
- 表格 > 列表 > 段落
- 约束解释 Why（"不超过 X，因为..."）

**Step 2.5 — 复杂任务处理：**
- 如果任务包含 2+ 个独立子功能 → 设计命令表
- 如果任务需要 3+ 步 → 使用 Multi-Pass 模式
- 如果是单一简单任务 → 保持单步结构

**Step 2.6 — 三层架构判断：**
- 如果 Skill 包含可确定性执行的逻辑 → 提取到 scripts/
- 如果 Skill 需要领域知识 → 提取到 reference/
- 简单 Skill（< 80 行）不需要分层，保持单文件

> **脚本优先原则**：能用脚本做的事不要写在指令里。

**Step 2.7 — Tool Usage 表生成：**

为生成的 Skill 创建 Tool Usage 表，只列出实际需要的工具，标注使用阶段和目的。

**Step 2.8 — 反模式检查：**

> **v09 新增**：生成后立即检查是否踩中已知反模式。

```
Read reference/anti-patterns.md → 逐项比对
```

| 反模式 | 症状 | 修正 |
|--------|------|------|
| 万能 Skill | description 过于宽泛，试图覆盖一切 | 收窄范围，拆分为多个 Skill |
| 复读机 | 大段复述用户输入而非处理 | 删除复述，直接输出结果 |
| 教科书型 | 花大量 token 解释基础概念 | 删除解释，Agent 已知这些 |
| 模糊约束 | "合适的"、"恰当的"、"必要时" | 用具体数字或条件替代 |
| 工具遗漏 | 指令中提到工具但 Tool Usage 表未列 | 同步更新 Tool Usage 表 |
| 过度分层 | < 80 行的 Skill 也搞三层架构 | 合并回单文件 |

### Pass 3 — 验证与交付

**工具**：Bash → Write

**Step 3.1 — 自动验证：**

```bash
bash scripts/validate_skill.sh <生成的 SKILL.md 路径>
```

**Step 3.2 — 质量清单：**

> **v09 新增**：10 项质量清单，逐项打分。

| # | 检查项 | 标准 |
|---|--------|------|
| 1 | Description | What+When+Keywords，50-150 字 |
| 2 | 角色声明 | 一句话定位，明确专业领域 |
| 3 | 步骤编号 | 每步一件事，步骤间有逻辑顺序 |
| 4 | 输出格式 | 明确、具体、可验证 |
| 5 | 约束+Why | 每条约束都解释了原因 |
| 6 | 命令表 | 动词优先、正交（如有） |
| 7 | Tool Usage | 完整且与指令一致 |
| 8 | 三层架构 | 确定性逻辑在 scripts/，知识在 reference/（如适用） |
| 9 | 反模式 | 不包含已知反模式 |
| 10 | Guardrails | 不违反硬性边界 |

全部通过 → 输出最终版本。任一失败 → 修正后重新检查该项。

**Step 3.3 — 保存交付：**

```
Write → ~/.qoder/skills/<skill-name>/SKILL.md
Write → ~/.qoder/skills/<skill-name>/scripts/... (如需要)
Write → ~/.qoder/skills/<skill-name>/reference/... (如需要)
```

---

## `/skill-creator review <path>`

**工具**：Read → Glob → Bash

**Pipeline：**
```
Glob <path>/**/* → 发现文件结构
Read <path>/SKILL.md → 获取内容
Bash scripts/validate_skill.sh <path>/SKILL.md → 自动检查
手动审查 → 输出报告
```

按以下维度审查（使用 Pass 3 的 10 项质量清单 + 反模式检查）：

| 维度 | 检查点 |
|------|--------|
| Description | What+When+Keywords 三步法？长度 50-150 字？ |
| 指令结构 | 是否有角色、步骤、输出格式、约束？ |
| 可执行性 | 步骤是否具体可操作？有无模糊表述？ |
| 约束质量 | 每条约束是否解释了原因？ |
| 命令设计 | 命令是否动词优先、正交？ |
| 架构分层 | 确定性逻辑是否提取到 scripts/？ |
| 工具使用 | Tool Usage 表完整且与指令一致？ |
| 反模式 | 是否命中 reference/anti-patterns.md 中的已知模式？ |
| Guardrails | 是否违反硬性边界？ |

输出格式：每个维度给出 Pass/Fail + 具体问题 + 改进建议。

---

## `/skill-creator improve <path>`

**工具**：Read → Edit

1. 先执行 `review` 获取审查结果
2. 针对每个 Fail 项生成修改方案
3. 展示修改方案，请用户确认
4. 用 Edit 工具应用局部修改，输出改进后的 SKILL.md

---

## I/O 示例

### 输入（用户回答）

```
1. 做什么：为 Git commit 生成规范化的 message
2. 场景：用户完成代码修改后、git add 之后
3. 输入：git diff --staged 的输出
4. 输出：一条符合 Conventional Commits 的 message
5. 约束：必须是英文，type 限定为 feat/fix/refactor/docs/test/chore
```

### 输出（生成的 SKILL.md）

```yaml
---
name: commit-message
description: >
  Generate Conventional Commits messages from staged changes.
  Use after git add when the user wants a commit message,
  asks to commit, or needs to describe their changes.
---
```
```markdown
# Commit Message Generator

你是一个 Git 提交规范专家。

## Tool Usage

| Tool | When | Purpose |
|------|------|---------|
| Bash | Step 1 | 运行 git diff --staged |

## 执行步骤

1. 运行 `git diff --staged` 获取变更内容
2. 分析变更的**意图**（新功能/修复/重构/文档/测试/杂项）
3. 确定影响范围（scope）
4. 生成 `<type>(<scope>): <subject>` 格式的 message
5. 如变更复杂，添加 body 段落说明 why

## 输出格式

直接输出可用的 commit message，不加多余解释。

## 约束

- type 限定为 feat/fix/refactor/docs/test/chore，因为这是 Conventional Commits 标准
- subject 不超过 50 字符，因为 GitHub 会截断更长的标题
- 使用英文，因为开源项目的通用语言是英文
- 不要解释什么是 Conventional Commits，因为这是基础知识
```

### 反例（差的 Skill）

```yaml
---
name: commit
description: 帮写 commit message
---

帮用户写 commit message。看看改了什么，然后写一个合适的 message。
```

**为什么差**：description 过短（欠触发）；无结构、无约束、"合适的"是模糊表述（模糊约束反模式）。

---

## 输出格式

生成的 SKILL.md 必须包含：
- YAML Frontmatter（name + description）
- `## Tool Usage` 表
- `## 执行步骤` 或 Multi-Pass 工作流
- `## 输出格式`
- `## 约束`

如果需要分层：
- `scripts/` 目录：可执行脚本（shebang + `set -e` + stdout JSON + stderr status）
- `reference/` 目录：知识文档（Markdown，供 Agent 用 Read 查阅）

## 约束

- 生成的 SKILL.md 不超过 200 行，因为过长会占用过多上下文窗口
- 不要解释 Agent 已知的基础知识，因为这浪费 token
- description 长度 50-150 字，因为这是 Layer 1 的 token 预算
- name 使用 kebab-case，因为这是跨平台目录命名惯例
- 如果任务需要多步，使用 Multi-Pass 模式而非单步，因为分步执行更可控
- 每个 I/O 示例必须是完整可运行的 SKILL.md，因为截断的示例会误导模型
- scripts/ 必须使用 `set -e`，因为静默失败导致错误输出被当作正确结果
- scripts/ 输出 JSON 到 stdout、状态到 stderr，因为这样 Agent 可以解析结构化数据
- Tool Usage 表必须与实际工具调用一致，因为不一致会误导审查

## 质量标准

- 生成的 Skill 应该是**可直接使用**的，不需要用户再修改
- 每个 Pass 有明确的输入和输出
- 关键步骤后有暂停点让用户确认
- 包含至少一个 I/O 示例和一个反例
- 分层 Skill 的 scripts/ 必须独立可运行
- 通过全部 10 项质量清单检查
- 不命中任何已知反模式
