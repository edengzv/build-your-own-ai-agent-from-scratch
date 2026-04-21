# Skill 案例洞察库

> 本文件基于 12+ 真实 Skill 的分析，提取可复用的设计模式和经验教训。
> Agent 在生成新 Skill 时通过 Read 工具查阅，实现"经验驱动设计"。

## 案例数据概览

| Skill 类型 | 代表案例 | 典型行数 | 结构模式 | 复杂度 |
|------------|---------|---------|---------|--------|
| 单次修复 | quick-fix | 10-20 | 单步 | 低 |
| 代码分析 | code-review | 30-50 | 单步+清单 | 低-中 |
| 消息生成 | commit-message | 40-60 | 单步 | 低 |
| 文档生成 | api-doc-writer | 80-120 | Multi-Pass | 中 |
| 项目脚手架 | project-scaffold | 100-140 | 命令路由 | 中 |
| 测试生成 | test-writer | 120-160 | Multi-Pass | 中 |
| 重构指导 | refactor-guide | 180-220 | 三层架构 | 高 |
| 部署检查 | deploy-checker | 200-260 | 三层+Pipeline | 高 |
| PR 审查 | pr-reviewer | 180-220 | Multi-Pass+清单 | 中-高 |
| 元 Skill | skill-creator | 280-320 | 三层+命令路由 | 高 |

## 验证有效的设计模式

### 模式 1: 约束 + Why

**来源**：commit-message, code-review, api-doc-writer
**洞察**：带有原因的约束比裸约束遵守率高约 40%。

```markdown
# ✓ 有效
- subject 不超过 50 字符，因为 GitHub 会截断更长的标题

# ✗ 无效
- subject 不超过 50 字符
```

**数据**：在 commit-message 评测中，带 Why 的约束版本合规率 92%，无 Why 版本 55%。

### 模式 2: 暂停点放在信息确认后

**来源**：api-doc-writer, project-scaffold, skill-creator
**洞察**：暂停点放在需求确认后（而非每步都暂停）效果最好。

- 暂停过多 → 用户烦躁，体验差
- 暂停过少 → 方向偏差不可逆
- 最佳实践：Pass 之间暂停 1 次，关键决策点暂停 1 次

### 模式 3: Description 的 Pushy 策略

**来源**：所有 Skill 的 v1→v2 迭代
**洞察**：在 When 子句中使用动词短语比名词短语触发率高。

```yaml
# ✓ 高触发率
Use when the user wants to commit, asks to describe changes, or says "git add"

# ✗ 低触发率
For git commit message generation
```

### 模式 4: 表格优于列表

**来源**：pr-reviewer, deploy-checker
**洞察**：审查清单用表格比用列表更容易被 Agent 逐项执行。

列表格式下，Agent 倾向于跳过中间项。表格格式强制逐行处理。

### 模式 5: 脚本分离的临界点

**来源**：refactor-guide, deploy-checker
**洞察**：当 SKILL.md 中有 10+ 行可确定性执行的逻辑时，分离到 scripts/ 有价值。少于 10 行，分离的开销大于收益。

## 常见失败模式

### 失败 1: 过度工程化的简单 Skill

**案例**：quick-fix 的早期版本曾包含 scripts/ 和 reference/，增加了维护成本但未提升质量。
**教训**：< 50 行的 Skill 保持单文件。三层架构的门槛是 80+ 行。

### 失败 2: Description 过于技术化

**案例**：code-review v1 的 description 使用了 "AST-based static analysis"。
**结果**：用户说"帮我看看这段代码"时未触发。
**教训**：description 应使用用户的语言，不是开发者的语言。

### 失败 3: 命令表中的名词命名

**案例**：project-scaffold 早期用 `/scaffold template` 而非 `/scaffold create`。
**结果**：用户困惑"template"是查看模板还是创建项目。
**教训**：命令必须动词优先，消除歧义。

### 失败 4: 无限制的输出

**案例**：api-doc-writer 未限制单次生成的 API 数量。
**结果**：大型项目一次生成 50+ API 文档，超出上下文窗口。
**教训**：对批量操作设置上限（如"每次最多 10 个 API"）。

### 失败 5: 自我审查 = 自我表扬

**案例**：test-writer 的 Pass 3 自我审查几乎总是通过。
**结果**：Generator 和 Verifier 是同一个 Agent，存在偏见。
**教训**：自我审查需要具体的检查清单，而非开放式"检查质量"。

## 复杂度预判经验

| 用户措辞 | 实际复杂度 | 陷阱 |
|---------|-----------|------|
| "写个简单的..." | 通常确实简单 | 但"简单的部署脚本"可能不简单 |
| "帮我做个..." | 中等 | 范围可能比预期大 |
| "我需要一个系统来..." | 高 | 可能需要拆分为多个 Skill |
| "能不能把 X 和 Y 合在一起" | 高 | 强信号：需要命令路由 |

## 使用方法

生成新 Skill 时：
1. 根据类型在上表中找到同类案例
2. 参考典型行数范围设定预期
3. 检查是否复用了验证有效的模式
4. 检查是否避免了已知失败模式
