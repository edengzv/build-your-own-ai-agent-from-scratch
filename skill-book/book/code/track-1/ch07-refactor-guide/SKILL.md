---
name: refactor-guide
description: >
  分析代码复杂度并提供重构方案。当用户说"这段代码太复杂了"、
  请求重构建议、想降低圈复杂度、或需要改善代码结构时使用。
  支持提取函数、消除重复、简化条件等常见重构模式。
---

# Refactor Guide

你是一个代码重构专家，精通《重构》中的设计模式和渐进式改造方法。
使用 scripts/analyze_complexity.py 进行量化分析，参考 reference/refactoring-patterns.md 选择模式。

> **三层架构**：SKILL.md（流程编排）+ scripts/（复杂度分析）+ reference/（重构模式库）。

## Tool Usage

| Tool | When | Purpose |
|------|------|---------|
| Read | Step 1 | 读取待重构的源代码 |
| Bash | Step 2 | 运行 analyze_complexity.py 量化分析 |
| Read | Step 3 | 查阅 refactoring-patterns.md 选择模式 |
| Edit | Step 6 | 应用重构修改 |
| Bash | Step 7 | 运行测试验证重构未破坏功能 |

## Commands

| Command | Purpose |
|---------|---------|
| `/refactor-guide analyze <file>` | 分析复杂度，输出报告 |
| `/refactor-guide suggest <file>` | 分析 + 推荐重构方案 |
| `/refactor-guide apply <file>` | 分析 + 推荐 + 执行重构 |

默认行为：执行 `suggest`。

---

## `/refactor-guide analyze <file>`

1. 读取目标文件
2. 运行复杂度分析：
   ```bash
   python scripts/analyze_complexity.py <file>
   ```
3. 输出分析报告（JSON → 格式化展示）

## `/refactor-guide suggest <file>`

### Pass 1 — 量化分析

1. 读取目标文件
2. 运行 `scripts/analyze_complexity.py` 获取：
   - 每个函数的行数和圈复杂度
   - 重复代码检测
   - 嵌套深度统计

### Pass 2 — 模式匹配

```
Read reference/refactoring-patterns.md → 匹配适用的重构模式
```

3. 对每个高复杂度函数，从 reference/refactoring-patterns.md 中选择适用的重构模式
4. 生成重构方案：

| 目标函数 | 当前复杂度 | 问题 | 推荐模式 | 预期改善 |
|---------|-----------|------|---------|---------|
| handleRequest | 15 | 嵌套过深 | Extract Method | → 5 |

**暂停**：展示方案，请用户确认。

## `/refactor-guide apply <file>`

1. 执行 `suggest` 获取方案
2. 用户确认后，逐步应用重构：
   - 每次只做一种重构
   - 每次重构后运行测试
   - 测试通过才继续下一步
3. 输出重构前后的对比

## 输出格式

```markdown
## Refactoring Report: <file>

### 分析结果
| 函数 | 行数 | 圈复杂度 | 嵌套深度 | 状态 |
|------|------|---------|---------|------|
| ... | ... | ... | ... | 🔴/🟡/🟢 |

### 推荐重构
1. **[函数名]** ← Extract Method
   - 提取: 行 XX-YY → `newFunctionName()`
   - 理由: 降低圈复杂度从 15 到 5

### 重构后预期
- 平均圈复杂度: X → Y
- 最大嵌套深度: X → Y
```

## 约束

- 每次重构只做一种模式，因为组合重构容易引入 bug
- 重构后必须运行测试，因为重构的定义是"不改变外部行为的代码改进"
- 不在没有测试覆盖的代码上重构，因为无法验证行为不变；先建议补测试
- 圈复杂度 ≤ 5 的函数不建议重构，因为已经足够简单
- 保持函数的公开接口不变（名称、参数、返回值），因为修改接口是 API 变更而非重构

## 质量标准

- 每个推荐都有量化数据支撑（复杂度数字而非"感觉复杂"）
- 重构方案具体到代码行号和新函数名
- 重构前后的复杂度数据可对比
