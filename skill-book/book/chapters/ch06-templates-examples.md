# Chapter 6: 模板与示例

> **Motto**: "一个好的示例胜过十段解释"

> 指令告诉 Agent "做什么"，但模板和示例告诉它"做成什么样"。你已经在 Chapter 3 的 `commit-message` Skill 中用了简单示例。本章系统性地教你三种锚定技巧，彻底消除输出的不确定性。

![Chapter 6: 模板与示例](images/ch06-templates-examples.png)

## The Problem

你写了一个测试生成 Skill："为给定的 Python 函数生成 pytest 单元测试"。Agent 每次生成的测试风格都不同：

- 第一次用 `unittest.TestCase` 类
- 第二次用纯 `pytest` 函数
- 第三次 mock 了一切
- 第四次测试了实现细节而不是行为

指令里写了"使用 pytest"，但没有告诉 Agent **怎样的 pytest 测试才是你想要的**。

## The Solution

**示例锚定（Example Anchoring）** 是通过具体的输入/输出对来固定 Agent 行为的技巧。比起抽象的描述，Agent 从示例中学习模式的效率远高于从规则中推导。

三种锚定方式：

1. **输入/输出示例**：给一个输入 → 展示期望的输出
2. **输出模板**：固定格式框架，变量部分用占位符
3. **反例**：展示错误的输出 + 解释为什么错

## 6.1 输入/输出示例

最直接的锚定方式——给 Agent 看"这是输入，这是我期望的输出"：

```markdown
## 示例

### 输入

```python
def calculate_discount(price: float, percentage: float) -> float:
    """Apply a percentage discount to a price."""
    if percentage < 0 or percentage > 100:
        raise ValueError("Percentage must be between 0 and 100")
    return price * (1 - percentage / 100)
```

### 期望输出

```python
import pytest
from mymodule import calculate_discount


class TestCalculateDiscount:
    """Tests for calculate_discount function."""

    def test_basic_discount(self):
        assert calculate_discount(100, 10) == 90.0

    def test_zero_discount(self):
        assert calculate_discount(100, 0) == 100.0

    def test_full_discount(self):
        assert calculate_discount(100, 100) == 0.0

    def test_negative_percentage_raises(self):
        with pytest.raises(ValueError):
            calculate_discount(100, -1)

    def test_over_100_percentage_raises(self):
        with pytest.raises(ValueError):
            calculate_discount(100, 101)

    def test_float_precision(self):
        result = calculate_discount(10, 33.33)
        assert abs(result - 6.667) < 0.001
```

Agent 看到这个示例后学到的模式：
- 使用 `class TestXxx` 组织（不是散函数）
- 方法命名 `test_描述行为`
- 测试覆盖：正常路径、边界条件、异常处理
- 浮点比较用 `abs(x - y) < epsilon`
- import 被测函数

**示例数量**：2-3 个不同复杂度的示例就足够了。太多示例会占用大量 tokens，边际效益递减。

## 6.2 输出模板

当你需要固定的输出格式时，模板比示例更高效：

```markdown
## 输出模板

每个测试文件遵循以下结构：

```python
import pytest
from {module} import {function_name}


class Test{FunctionNamePascalCase}:
    """{one-sentence description of what is being tested}."""

    # --- Happy path ---

    def test_{basic_scenario}(self):
        {assertion}

    def test_{another_normal_case}(self):
        {assertion}

    # --- Edge cases ---

    def test_{boundary_condition}(self):
        {assertion}

    # --- Error cases ---

    def test_{error_scenario}_raises(self):
        with pytest.raises({ExceptionType}):
            {call_that_should_fail}
```

模板中的 `{变量}` 告诉 Agent 哪些部分需要替换，哪些部分是固定的。Agent 学到：

- import 格式是固定的
- 测试分三组：happy path / edge cases / error cases
- 错误测试的方法名以 `_raises` 结尾
- 使用注释分隔测试组

## 6.3 反例

反例告诉 Agent "不要这样做"：

```markdown
## 反例：不要这样写测试

### 反例 1: 测试实现而非行为

```python
# 坏：这是在测试内部实现
def test_discount_implementation():
    result = calculate_discount(100, 10)
    # 测试内部计算步骤
    assert (1 - 10/100) == 0.9
    assert 100 * 0.9 == result
```

为什么不好：测试应该验证**输出**是否正确，不应该重复**内部计算逻辑**。如果实现改了（比如换了计算顺序），测试不应该因此失败。

### 反例 2: 过度 mock

```python
# 坏：mock 了被测函数本身的依赖
@mock.patch('mymodule.float.__mul__')
def test_discount_with_mock(mock_mul):
    mock_mul.return_value = 90.0
    assert calculate_discount(100, 10) == 90.0
```

为什么不好：Mock 基础运算让测试失去了验证价值。只 mock 外部依赖（数据库、API），不要 mock 纯计算。

### 反例 3: 无断言

```python
# 坏：运行了但什么都没验证
def test_discount_runs():
    calculate_discount(100, 10)  # 没有 assert
```

为什么不好：这个测试只验证了"不崩溃"，不验证"结果正确"。
```

反例的威力在于：Agent 在生成输出前会"检查"自己的输出是否像反例中的样子。如果像，它会自动调整。

## 6.4 完整的 test-writer Skill

综合三种锚定方式，这是完整的 `test-writer` Skill：

```markdown
---
name: test-writer
description: 为 Python 函数生成 pytest 单元测试。分析函数签名和行为，生成覆盖正常路径、边界条件和错误处理的测试用例。当用户请求写测试或生成测试用例时使用。
---

# Test Writer

为 Python 函数生成高质量的 pytest 单元测试。

## 执行步骤

1. 读取目标函数的源代码
2. 分析函数签名（参数类型、返回类型、默认值）
3. 分析函数行为：
   - 正常执行路径有哪些？
   - 边界条件是什么？（空输入、零值、最大值）
   - 什么情况下会抛异常？
4. 按输出模板生成测试
5. 确保每个测试方法测试**一个行为**

## 输出模板

[模板内容如 6.2 节]

## 示例

[输入/输出示例如 6.1 节]

## 反例

[反例如 6.3 节]

## 约束

- 每个函数生成 5-10 个测试用例
- 不要 mock 纯计算函数的内部依赖
- 浮点比较使用 pytest.approx() 或 abs 差值
- 测试方法名必须描述被测试的行为，不是实现
```

## 6.5 案例解剖：wechat-tech-card 的模板系统

`wechat-tech-card` Skill 把模板发挥到了极致。它有 5 种卡片类型，每种都有独立的 HTML 模板文件：

```
templates/
├── concept-explainer.html    → 概念解释卡
├── comparison.html           → 对比卡
├── architecture.html         → 架构卡
├── timeline.html             → 时间线卡
└── cheatsheet.html           → 速查卡
```

SKILL.md 中用命令路由到不同模板：

```markdown
当执行 `concept` 命令时：
1. 收集内容（见 Pass 1）
2. 读取 `templates/concept-explainer.html`
3. 用收集的内容填充模板变量
4. 通过 show_widget 渲染
```

模板变量使用明确的占位符：

```html
<h1 class="title">{TOPIC}</h1>
<p class="definition">{ONE_LINE_DEFINITION}</p>
<div class="key-points">
  {KEY_POINTS_HTML}
</div>
```

这种设计的优势：
- **一致性**：所有概念卡都有相同的视觉布局
- **可维护**：改模板不用改 Skill 指令
- **可扩展**：加新卡片类型只需加一个模板文件

## 6.6 示例设计原则

### 原则 1: 代表性

示例应该覆盖**典型场景**，不只是最简单的 hello world：

```markdown
# 坏：只有最简单的情况
示例：为 add(a, b) 函数写测试

# 好：覆盖了常见复杂度
示例 1：纯计算函数（calculate_discount）
示例 2：带状态的函数（user.update_profile）
```

### 原则 2: 多样性

示例之间应该展示**不同的决策路径**：

```markdown
# 坏：两个示例差不多
示例 1：为 add(a, b) 写测试
示例 2：为 subtract(a, b) 写测试

# 好：展示不同的测试策略
示例 1：纯函数 → 直接断言
示例 2：抛异常函数 → pytest.raises
```

### 原则 3: 简洁性

示例越短越好——只保留教学必需的部分：

```markdown
# 坏：示例函数太长（30 行），淹没了测试模式
# 好：示例函数 5-10 行，测试模式一目了然
```

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| Agent 每次输出格式不同 | 模板固定了输出结构 |
| 只能描述"不要做什么" | 反例具体展示了"什么是错的" |
| 示例只是简单的 hello world | 示例覆盖了典型场景和决策分支 |

**Cumulative capability**: 你的 `test-writer` Skill 使用了三种锚定方式，输出一致性和质量显著提升。

## Try It Yourself

> 完整代码见 `code/track-1/ch06-test-writer/`，可直接复制到 `~/.qoder/skills/` 使用。
>
> **Track 2 演进**：对比 `code/track-2/v05-commands/` 和 `code/track-2/v06-examples/` 的 diff，
> 观察 I/O 示例和反例如何从 134 行扩展到 202 行。

1. **Verify**: 用 `test-writer` 为一个真实项目的函数生成测试，检查输出是否符合模板。
2. **Extend**: 给 Chapter 3 的 `commit-message` Skill 添加第 3 个不同场景的示例（如 refactor 类型）。对比添加前后输出的一致性。
3. **Explore**: 找一个你觉得输出不稳定的 Skill。诊断原因：是缺少示例、缺少模板、还是缺少反例？添加最缺的那种锚定方式。

## Summary

- 三种锚定方式：**输入/输出示例、输出模板、反例**
- 示例锚定是最强的行为固定手段——Agent 从示例中学习模式的效率远高于规则
- 输出模板用 `{变量}` 标记可替换部分，固定整体结构
- 反例告诉 Agent "不要这样做" + "为什么不好"
- 示例设计原则：**代表性**（典型场景）、**多样性**（不同决策路径）、**简洁性**（最短有效）
- 2-3 个精心设计的示例胜过 10 个随意的示例

## Further Reading

- Few-shot learning 的原理：为什么示例对 LLM 如此有效
- 第 7 章《渐进式加载》——当示例太多太长时，可以放到 reference/ 目录
- 第 9 章《质量检查清单》——用 checklist 补充示例无法覆盖的场景
