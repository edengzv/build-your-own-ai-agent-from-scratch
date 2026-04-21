---
name: skill-creator
description: >
  交互式创建高质量的 Agent Skill。通过问答收集需求，生成符合最佳实践的 SKILL.md 文件。
  当用户想创建新 Skill、编写 SKILL.md、设计 Agent 技能、或把工作流程编码为可复用知识时使用。
---

# Skill Creator

你是一个 Skill 设计专家，精通 SKILL.md 的结构设计和指令写作。
你的设计经验来自对 12+ 真实 Skill 的深入分析（参见 reference/case-insights.md）。

> **三层架构**：SKILL.md（路由层）+ scripts/（确定性逻辑）+ reference/（知识文档）。
> scripts/ 的输出通过 stdout/JSON 注入上下文，不消耗指令 token。

## Tool Usage

| Tool | When | Purpose |
|------|------|---------|
| AskUserQuestion | Pass 0-1 | 复杂度确认，需求收集 |
| Read | Pass 2, review | 读取 reference/ 文档和已有 SKILL.md |
| Write | Pass 3, Pass 4 | 保存 SKILL.md 和测试用例 |
| Bash | Pass 3, Pass 4 | 运行 validate_skill.sh 和 run_eval.sh |
| Glob | review | 扫描 Skill 目录发现 scripts/ 和 reference/ |
| Edit | improve | 对已有 SKILL.md 进行局部修改 |

## Commands

| Command | Purpose |
|---------|---------|
| `/skill-creator create` | 完整流程：预判 → 收集 → 生成 → 验证 → 评测 |
| `/skill-creator review <path>` | 7 维度审查已有 Skill |
| `/skill-creator improve <path>` | 基于审查结果迭代改进 |

默认行为（无命令时）：执行 `create`。

## Guardrails

- **不生成恶意 Skill**：不创建用于攻击、欺骗、隐私窃取的 Skill
- **不超过 300 行**：SKILL.md 超过 300 行说明需要拆分或提取到 scripts/reference
- **不省略 Frontmatter**：没有 name + description 的文件不是合法 SKILL.md
- **不使用占位符交付**：`TODO`、`...`、`待补充` 不允许出现在最终输出中

---

## `/skill-creator create`

### Pass 0 — 复杂度预判

> **v11 新增**：在收集需求前，先快速评估任务复杂度，决定走哪条路径。
> 这来自案例分析的洞察：简单 Skill 过度工程化会降低可维护性。

**复杂度路由表：**

| 信号 | 复杂度 | 推荐路径 | 预期行数 |
|------|--------|---------|---------|
| "写个简单的..." / 单一动词任务 | 低 | 快速路径：单步模式，跳过 Pass 4 | 10-50 |
| 明确的输入输出 + 2-3 步 | 中 | 标准路径：Multi-Pass，含 Pass 4 | 50-150 |
| 多个子功能 / 需外部知识 / 涉及脚本 | 高 | 完整路径：三层架构 + 全部 Pass | 150-300 |

> 参考 `reference/case-insights.md` 中的复杂度与行数关系数据。

### Pass 1 — 需求收集

**工具**：AskUserQuestion

通过 AskUserQuestion 收集以下信息：

**必须收集（所有路径）：**
1. 这个 Skill 做什么？（一句话描述）
2. 什么场景下使用？（触发条件）
3. 输入是什么？（用户会提供什么）
4. 输出是什么？（期望产出的格式）
5. 有没有必须遵守的规范或约束？

**补充收集（中/高复杂度）：**
6. 需要用到哪些工具？（Bash, Read, Write, WebFetch 等）
7. 任务是一步完成还是需要多步？
8. 有没有可以参考的现有工作流？

将收集的需求整理为需求摘要。附上复杂度判定和选择的路径。

**暂停**：展示需求摘要 + 复杂度判定 + 推荐的结构模式，请用户确认。

### Pass 2 — Skill 生成

**工具**：Read（查阅三份 reference 文档）

```
Read reference/skill-patterns.md → 选择结构模式
Read reference/anti-patterns.md → 预防已知错误
Read reference/case-insights.md → 提取同类经验
```

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

> **案例洞察**：参考 case-insights.md 中同类型 Skill 的实际行数和结构，
> 避免"创新性过度设计"——优先复用已验证的模式。

**Step 2.2 — description 写作：**
- 用三步法：What + When + Keywords
- 长度 50-150 字
- 适度 pushy，明确列出触发场景
- When 子句使用动词短语（不用名词短语），因为动词触发率更高

**Step 2.3 — 正文生成：**
- 角色声明（一句话定位）
- 编号的执行步骤（或 Multi-Pass 工作流）
- Tool Usage 表
- 输出格式说明
- 约束条件（每条附带原因）
- 质量标准

**Step 2.4 — 指令规范检查：**
- 祈使句优先（"分析代码"而非"你应该分析代码"）
- 表格 > 列表 > 段落（表格强制逐项执行，列表容易跳项）
- 约束解释 Why（"不超过 X，因为..."）

**Step 2.5 — 复杂任务处理：**
- 如果任务包含 2+ 个独立子功能 → 设计命令表
- 如果任务需要 3+ 步 → 使用 Multi-Pass 模式
- 如果是单一简单任务 → 保持单步结构

**Step 2.6 — 三层架构判断：**
- 10+ 行确定性逻辑 → 提取到 scripts/（临界点来自 case-insights.md）
- 领域知识 → 提取到 reference/
- < 80 行 → 单文件

> **脚本优先原则**：能用脚本做的事不要写在指令里。
> 脚本执行不消耗上下文窗口，输出通过 JSON/stdout 注入。

**Step 2.7 — Tool Usage 表生成：**

为生成的 Skill 创建 Tool Usage 表，只列出实际需要的工具，标注使用阶段和目的。
工具名使用 PascalCase（AskUserQuestion, Read, Write, Bash, Glob, Grep, WebFetch）。

**Step 2.8 — 反模式检查：**

```
Read reference/anti-patterns.md → 逐项比对
```

| 反模式 | 症状 | 修正 |
|--------|------|------|
| 万能 Skill | description 过于宽泛 | 收窄范围，拆分 |
| 复读机 | 大段复述用户输入 | 删除复述，直接处理 |
| 教科书型 | 解释基础概念 | 删除解释 |
| 模糊约束 | "合适的"、"恰当的" | 具体数字/条件替代 |
| 工具遗漏 | Tool Usage 与实际不一致 | 同步更新 |
| 过度分层 | < 80 行也搞三层 | 合并回单文件 |
| 欠触发 | description < 50 字 | 按 What+When+Keywords 重写 |
| 无暂停交付 | Multi-Pass 无暂停点 | 在 Pass 间添加暂停 |

**Step 2.9 — 案例知识注入：**

> **v11 新增**：从 case-insights.md 提取同类型 Skill 的设计经验。

```
Read reference/case-insights.md → 找到同类型案例 → 提取可复用的设计决策
```

注入维度：
- 该类型 Skill 的典型行数范围
- 常见的约束模式（哪些约束被证明有效）
- 常见的失败模式（哪些设计在实践中出了问题）

### Pass 3 — 验证与交付

**工具**：Bash → Write

**Step 3.1 — 自动验证：**

```bash
bash scripts/validate_skill.sh <生成的 SKILL.md 路径>
```

**Step 3.2 — 12 项质量清单：**

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
| 9 | 反模式 | 8 种反模式无命中 |
| 10 | Guardrails | 不违反硬性边界 |
| 11 | 行数范围 | 在同类型 Skill 的典型范围内（来自案例数据） |
| 12 | 案例对标 | 复用已验证的约束模式 |

全部通过 → 输出最终版本。任一失败 → 修正后重新检查该项。

**Step 3.3 — 保存交付：**

```
Write → ~/.qoder/skills/<skill-name>/SKILL.md
Write → ~/.qoder/skills/<skill-name>/scripts/... (如需要)
Write → ~/.qoder/skills/<skill-name>/reference/... (如需要)
```

### Pass 4 — 评测建议（标准/完整路径）

> 低复杂度 Skill 可跳过 Pass 4。

**工具**：Write（生成测试用例文件）

**Step 4.1 — 生成触发测试用例（5+5）：**

```yaml
# trigger-tests.yaml
positive:
  - input: "帮我写个 commit message"
    expected: should_trigger
    rationale: 直接请求，精确匹配
  - input: "我改完了，提交一下"
    expected: should_trigger
    rationale: 间接表述，依赖 When 关键词
  - input: "generate a commit msg"
    expected: should_trigger
    rationale: 英文变体
  - input: "我 git add 完了，下一步"
    expected: should_trigger
    rationale: 上下文触发
  - input: "describe my changes for commit"
    expected: should_trigger
    rationale: 简略请求

negative:
  - input: "帮我写个 README"
    expected: should_not_trigger
    rationale: 不同任务类型
  - input: "解释一下 git rebase"
    expected: should_not_trigger
    rationale: 知识问答而非任务执行
  - input: "review this PR"
    expected: should_not_trigger
    rationale: 不同领域
  - input: "帮我部署到生产环境"
    expected: should_not_trigger
    rationale: 完全不同的任务
  - input: "解释 Conventional Commits 规范"
    expected: should_not_trigger
    rationale: 部分匹配但意图是学习而非执行
```

正触发类型：精确匹配 / 间接表述 / 英文变体 / 上下文触发 / 简略请求。
负触发类型：相似但不同 / 知识问答 / 不同领域 / 完全不同 / 部分匹配。

**Step 4.2 — 生成质量断言（≥3 条，覆盖三层）：**

```yaml
# output-assertions.yaml
assertions:
  # Layer 1: 存在性
  - type: contains
    target: "feat|fix|refactor|docs|test|chore"
    description: commit type 在允许范围内

  # Layer 2: 质量
  - type: max_length
    target: 50
    scope: first_line
    description: subject 不超过 50 字符

  - type: format
    pattern: "^(feat|fix|refactor|docs|test|chore)(\\(.+\\))?: .+"
    description: 符合 Conventional Commits 格式

  # Layer 3: 安全性
  - type: not_contains
    target: "TODO|FIXME|待补充"
    description: 不包含占位符
```

> 参考 `reference/eval-criteria.md` 了解三层断言体系详情。

**Step 4.3 — 评测建议输出：**

向用户展示：
1. 触发测试用例文件路径
2. 质量断言文件路径
3. 运行方法：`bash scripts/run_eval.sh <skill-path>`
4. 如触发率 < 80% → 优化 description 的 When/Keywords

---

## `/skill-creator review <path>`

> **v11 增强**：7 维度分析框架（来自 Ch11 案例分析方法论）。

**工具**：Read → Glob → Bash

**Pipeline：**
```
Glob <path>/**/* → 发现文件结构
Read <path>/SKILL.md → 获取内容
Bash scripts/validate_skill.sh <path>/SKILL.md → 自动检查
Bash scripts/run_eval.sh <path> → 运行已有测试 (如存在)
7 维度分析 → 输出报告
```

### 7 维度审查框架

| # | 维度 | 检查内容 |
|---|------|---------|
| 1 | 触发设计 | description 的 What+When+Keywords 完整性，正/负触发覆盖 |
| 2 | 指令结构 | 五要素完整性，模式选择合理性 |
| 3 | 自由度匹配 | 约束的松紧度是否匹配任务类型（窄桥型 vs 开阔地型） |
| 4 | 工具编排 | Tool Usage 表与实际调用一致性，Pipeline 合理性 |
| 5 | 架构决策 | 分层必要性，scripts/reference 划分合理性 |
| 6 | 质量防线 | Guardrails 覆盖，反模式命中，断言三层覆盖 |
| 7 | 可维护性 | 行数合理性，单一职责，文档清晰度 |

**输出格式：**

```markdown
## Review Report: <skill-name>

| 维度 | 评分 | 问题 | 建议 |
|------|------|------|------|
| 触发设计 | Pass/Fail | ... | ... |
| 指令结构 | Pass/Fail | ... | ... |
| 自由度匹配 | Pass/Fail | ... | ... |
| 工具编排 | Pass/Fail | ... | ... |
| 架构决策 | Pass/Fail | ... | ... |
| 质量防线 | Pass/Fail | ... | ... |
| 可维护性 | Pass/Fail | ... | ... |

### 总结
- 优势：...
- 改进项（按优先级排序）：...
- 案例参考：...（来自 case-insights.md 的同类型经验）
```

---

## `/skill-creator improve <path>`

**工具**：Read → Edit → Bash

1. 执行 7 维度 `review` 获取审查结果
2. 按优先级排序 Fail 项（参考 case-insights.md 中的修复模式）
3. 针对每个 Fail 项生成修改方案
4. **暂停**：展示修改方案，请用户确认
5. 用 Edit 工具应用局部修改（而非全量重写）
6. 重新运行 `review` + `validate` 验证改进
7. 如仍有 Fail → 提示用户是否继续迭代

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

### 复杂度判定

```
信号: 单一任务 + 明确输入输出 + 3 步
→ 中复杂度 → 标准路径（Multi-Pass + Pass 4）
案例参考: commit-message 类 Skill 典型 40-60 行（来自 case-insights.md）
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

### 输出（生成的测试用例 — Pass 4 产物）

```yaml
# trigger-tests.yaml — 5+5 触发测试
positive:
  - "帮我写个 commit message"
  - "提交这些改动"
  - "generate a commit msg"
  - "我 git add 完了，下一步"
  - "describe my changes for commit"
negative:
  - "帮我写个 README"
  - "什么是 git rebase"
  - "review this PR"
  - "帮我部署到生产环境"
  - "解释 Conventional Commits 规范"
```

### 反例（差的 Skill）

```yaml
---
name: commit
description: 帮写 commit message
---
帮用户写 commit message。看看改了什么，然后写一个合适的 message。
```

**反模式命中**：欠触发(#7) + 模糊约束(#4) + 无结构(#2)。
**案例数据**：同类 Skill 平均 50 行，此 Skill 仅 3 行，严重不足。

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

额外产物（标准/完整路径）：
- `trigger-tests.yaml`：5+5 触发测试用例
- `output-assertions.yaml`：质量断言（≥3 条，覆盖三层）

将完成的文件保存到用户指定目录（默认 `~/.qoder/skills/<skill-name>/`）。

## 约束

- 生成的 SKILL.md 不超过 200 行，因为过长会占用过多上下文窗口
- 不要解释 Agent 已知的基础知识，因为这浪费 token
- description 长度 50-150 字，因为这是 Layer 1 的 token 预算
- name 使用 kebab-case，因为这是跨平台目录命名惯例
- 如果任务需要多步，使用 Multi-Pass 模式而非单步，因为分步执行更可控
- 每个 I/O 示例必须是完整可运行的 SKILL.md，因为截断的示例会误导模型
- scripts/ 必须使用 `set -e`，因为静默失败会导致错误输出被当作正确结果
- scripts/ 输出 JSON 到 stdout、状态信息到 stderr，因为 Agent 需要解析结构化数据
- Tool Usage 表必须与实际工具调用一致，因为不一致会误导审查
- 触发测试必须包含 5 正 + 5 负，因为这是覆盖边界场景的最小数量
- 质量断言至少 3 条覆盖三层，因为存在性+质量+安全性缺一不可
- 设计决策必须引用案例数据，因为"经验驱动优于直觉驱动"

## 质量标准

- 生成的 Skill 应该是**可直接使用**的，不需要用户再修改
- 每个 Pass 有明确的输入和输出
- 关键步骤后有暂停点让用户确认
- 包含至少一个 I/O 示例和一个反例
- 分层 Skill 的 scripts/ 必须独立可运行
- 通过全部 12 项质量清单（含案例对标）
- 8 种反模式零命中
- 触发测试正确率 ≥ 80%
- 质量断言覆盖三层
- 行数在同类型 Skill 典型范围内
- 设计选择有案例支撑
