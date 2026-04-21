# 重构模式参考

> 本文件供 Agent 在分析代码后选择合适的重构模式。按复杂度症状索引。

## 症状 → 模式速查

| 症状 | 推荐模式 | 适用条件 |
|------|---------|---------|
| 函数过长（> 30 行） | Extract Method | 可识别出独立的代码块 |
| 嵌套过深（> 3 层） | Guard Clause / Extract Method | if-else 层层嵌套 |
| 重复代码 | Extract Function + 参数化 | 两处以上相似逻辑 |
| 过多参数（> 4 个） | Introduce Parameter Object | 参数经常一起出现 |
| Switch/Case 过长 | Replace with Polymorphism / Strategy | 多个类型走不同逻辑 |
| 临时变量链 | Replace Temp with Query | 变量只用一次且可计算 |

## 模式详解

### Extract Method

**何时用**：函数中有一段代码可以用"做什么"来命名。

```python
# Before
def process_order(order):
    # validate
    if not order.items:
        raise ValueError("Empty order")
    if order.total < 0:
        raise ValueError("Invalid total")
    # calculate
    subtotal = sum(item.price for item in order.items)
    tax = subtotal * 0.1
    total = subtotal + tax
    # save
    db.save(order)

# After
def process_order(order):
    validate_order(order)
    total = calculate_total(order)
    db.save(order)
```

**关键点**：新函数名应描述"做什么"而非"怎么做"。

### Guard Clause

**何时用**：函数开头有多层嵌套的条件检查。

```python
# Before
def get_payment(order):
    if order:
        if order.is_paid:
            if order.payment:
                return order.payment
    return None

# After
def get_payment(order):
    if not order:
        return None
    if not order.is_paid:
        return None
    if not order.payment:
        return None
    return order.payment
```

**关键点**：提前返回，让主逻辑保持在最低嵌套层。

### Introduce Parameter Object

**何时用**：多个函数接收相同的一组参数。

```python
# Before
def create_user(name, email, age, role, department):
    ...

# After
@dataclass
class UserProfile:
    name: str
    email: str
    age: int
    role: str
    department: str

def create_user(profile: UserProfile):
    ...
```

### Replace with Strategy

**何时用**：一个大的 switch/case 或 if-elif 链处理不同类型。

```python
# Before
def calculate_shipping(method, weight):
    if method == 'standard':
        return weight * 5
    elif method == 'express':
        return weight * 10 + 15
    elif method == 'overnight':
        return weight * 20 + 30

# After
SHIPPING_STRATEGIES = {
    'standard': lambda w: w * 5,
    'express': lambda w: w * 10 + 15,
    'overnight': lambda w: w * 20 + 30,
}

def calculate_shipping(method, weight):
    strategy = SHIPPING_STRATEGIES.get(method)
    if not strategy:
        raise ValueError(f"Unknown method: {method}")
    return strategy(weight)
```

## 重构安全准则

1. **先有测试再重构**：没有测试覆盖的代码，先补测试
2. **一次一种模式**：不要同时做 Extract Method + Rename
3. **每步验证**：每次重构后运行测试
4. **保持接口不变**：重构不改变公开 API
