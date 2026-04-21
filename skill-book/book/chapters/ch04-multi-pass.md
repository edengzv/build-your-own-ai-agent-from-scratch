# Chapter 4: 工作流设计模式

> **Motto**: "把大象装进冰箱需要三步，好的 Skill 也是"

> 你的 Skill 工具箱里已经有了 3 个单步 Skill。但真实世界的任务——写文档、做审查、创建项目——往往需要更复杂的执行逻辑。本章你将学会 5 种工作流设计模式，并掌握根据任务特性选择最合适模式的方法。

![Chapter 4: 工作流设计模式](images/ch04-multi-pass.png)

## The Problem

你想写一个生成 API 文档的 Skill。直觉做法是：

```markdown
# API Doc Writer

阅读源代码中的 API 端点，为每个端点生成 OpenAPI 格式的文档，包含参数说明、响应格式、错误码和使用示例。
```

你让 Agent 对一个有 20 个端点的项目运行这个 Skill。Agent 输出了一份很长的文档——但问题来了：

- 有 3 个端点被遗漏了（Agent 在中途"忘了"）
- 参数说明和实际代码不一致（没有交叉验证）
- 你想先看端点列表再生成文档——但 Agent 已经全做完了
- 文档太长，超出了上下文窗口，后半部分质量明显下降

根本问题是：**你把一个多步骤任务压缩成了一步**。Agent 需要同时做"分析代码结构"、"理解每个端点"、"生成文档"、"格式化输出"四件事。认知负担太重，结果不可控。

## The Solution

**Multi-Pass（多步工作流）** 是把复杂任务拆成多个独立阶段的设计模式。每个 Pass：

- 只做**一件事**
- 有明确的**输入和输出**
- 输出可以被**用户检查**后再进入下一步

```
┌──────────┐    artifact    ┌──────────┐    artifact    ┌──────────┐
│  Pass 1  │──────────────→│  Pass 2  │──────────────→│  Pass 3  │
│ 分析结构  │  endpoint.md  │ 生成文档  │   draft.md   │ 格式整合  │
└──────────┘       ↑        └──────────┘               └──────────┘
                   │
              用户确认 ✓
```

Pass 之间通过**交接物（artifact）** 传递信息——通常是一个中间文件。关键 Pass 后设置**暂停点**，等待用户确认。

## 4.1 设计第一个 Multi-Pass Skill

让我们重写 `api-doc-writer` 为 3-Pass 版本：

```markdown
---
name: api-doc-writer
description: 为 REST API 项目生成 OpenAPI 格式的文档。分析路由代码，提取端点、参数、响应格式，生成结构化 API 文档。当用户需要生成或更新 API 文档时使用。
---

# API Documentation Writer

为 REST API 项目生成完整的 API 文档。采用三轮工作流确保准确性和完整性。

## 工作流程

### Pass 1 — 端点发现

1. 搜索项目中的路由定义文件（如 `routes/`, `api/`, `controllers/`）
2. 提取所有 API 端点，记录：
   - HTTP 方法（GET/POST/PUT/DELETE）
   - 路径（/api/users/:id）
   - 所在文件和行号
3. 输出端点清单到 `api-docs/endpoints.md`
4. **暂停**：告知用户发现了多少个端点，请用户确认清单是否完整

### Pass 2 — 文档生成

用户确认端点清单后，对每个端点：

1. 读取端点的完整实现代码
2. 提取：
   - 请求参数（path params, query params, body schema）
   - 响应格式（成功响应 + 错误响应）
   - 认证要求
   - 使用示例
3. 按 OpenAPI 风格生成文档
4. 输出到 `api-docs/draft.md`

### Pass 3 — 整合与格式化

1. 读取 `api-docs/draft.md`
2. 添加目录（Table of Contents）
3. 统一格式和术语
4. 检查交叉引用的一致性
5. 输出最终文档到 `api-docs/api-reference.md`

## 输出目录

api-docs/
├── endpoints.md        # Pass 1: 端点清单
├── draft.md            # Pass 2: 文档草稿
└── api-reference.md    # Pass 3: 最终文档

## 约束

- 每个端点的文档不超过 200 行
- 如果项目超过 50 个端点，按模块分文件输出
- 参数类型必须从代码中推断，不要猜测
```

这个 3-Pass 设计解决了之前的所有问题：

| 问题 | 单步版本 | 3-Pass 版本 |
|------|---------|------------|
| 遗漏端点 | Agent 中途遗忘 | Pass 1 先列出完整清单 |
| 参数不一致 | 没有验证步骤 | Pass 2 逐个端点读取代码 |
| 无法中途检查 | 一口气输出 | Pass 1 后暂停确认 |
| 上下文溢出 | 所有内容在一轮完成 | 分散到 3 轮，每轮有自己的焦点 |

## 4.2 Pass 设计原则

### 原则 1: 每个 Pass 只做一件事

```
# 坏：一个 Pass 做了三件事
Pass 1: 分析代码结构，为每个函数生成文档，然后格式化输出

# 好：三个 Pass 各做一件事
Pass 1: 分析代码结构，输出函数清单
Pass 2: 为每个函数生成文档
Pass 3: 格式化和整合
```

### 原则 2: 用交接文件传递信息

不要依赖 Agent 的"记忆"在 Pass 之间传递信息。写入文件可以确保信息不丢失：

```markdown
### Pass 1 — 输出到 `analysis.md`
### Pass 2 — 读取 `analysis.md`，输出到 `draft.md`
### Pass 3 — 读取 `draft.md`，输出到 `final.md`
```

### 原则 3: 在关键 Pass 后暂停

不是每个 Pass 都需要暂停。暂停的时机是：

- 后续工作量大，如果方向错了代价高
- 需要用户的判断（"这些端点完整吗？"）
- 涉及不可逆操作（写入文件、发送请求）

```markdown
### Pass 1 — 端点发现
...
4. **暂停**：请用户确认端点清单
```

### 原则 4: Pass 数量控制在 3-5 个

```
2 个 Pass: 几乎和单步没区别
3 个 Pass: 大多数任务的最佳选择
5 个 Pass: 复杂任务的上限
7+ 个 Pass: 太多了——Agent 会迷失在步骤中
```

> **Tip**: 如果你觉得需要 7 个 Pass，考虑把 Skill 拆成两个 Skill，每个 3-4 个 Pass。

## 4.3 案例解剖：wechat-article-writer 的 5-Pass 工作流

让我们看一个真实的复杂 Skill 是怎么设计工作流的。`wechat-article-writer` 把英文技术文章转化为中文微信公众号文章，采用了 5-Pass 设计：

```
Pass 1: 素材分析 (Source Analysis)
  ↓  输出 analysis.md → 暂停确认
Pass 2: 洞察综合 (Insight Synthesis)
  ↓  输出大纲 → 暂停确认
Pass 3: 正文撰写 (Drafting)
  ↓  输出 article.md
Pass 4: 配图制作 (Illustration)
  ↓  输出 cover.png + images/
Pass 5: 微信适配 (WeChat Polish)
  ↓  输出 article.html
```

为什么需要 5 个 Pass，而不是 3 个？

**Pass 1 和 Pass 2 不能合并**：分析是客观的（"原文说了什么"），综合是主观的（"我们的文章角度是什么"）。用户需要在分析结果的基础上决定文章方向——这个决策点不能跳过。

**Pass 3 和 Pass 4 不能合并**：写文字和生成图片是完全不同的任务，用到不同的工具（Write vs ImageGen）。混合在一起会让 Agent 在写作时频繁切换"模式"，降低两边的质量。

**Pass 5 不能省略**：微信平台有独特的格式限制（不支持的 HTML 标签、预览字数、互动引导）。这些平台适配逻辑如果混在正文撰写中，会干扰写作的流畅性。

关键设计决策：

- **两个暂停点**（Pass 1 后和 Pass 2 后）——因为这两个阶段决定了文章的整体方向
- **交接文件明确**——每个 Pass 的输出都写入独立文件
- **每个 Pass 的指令独立**——可以单独执行（通过命令路由，这是第 5 章的主题）

## 4.4 Multi-Pass 的变体模式

不是所有多步工作流都是简单的线性序列。以下是三个常见的变体：

### 变体 1: 带分支的工作流

```
Pass 1: 分析 → 判断类型
  ├─ 类型 A → Pass 2A: 处理方式 A
  └─ 类型 B → Pass 2B: 处理方式 B
Pass 3: 统一的输出格式
```

在 SKILL.md 中用条件语句表达：

```markdown
### Pass 2 — 根据类型处理

如果 Pass 1 判断为"新功能"：
  - 检查测试覆盖率
  - 验证文档更新
  - 检查 API 兼容性

如果 Pass 1 判断为"Bug 修复"：
  - 验证根因分析
  - 检查回归测试
  - 确认影响范围
```

### 变体 2: 循环工作流

```
Pass 1: 初始处理
Pass 2: 质量检查
  ├─ 通过 → Pass 3: 最终输出
  └─ 不通过 → 回到 Pass 1 修改（最多 3 次）
```

```markdown
### Pass 2 — 质量检查

对 Pass 1 的输出进行检查（见质量清单）。
如果发现问题，修改后重新检查。最多重复 3 次。
如果 3 次后仍有问题，输出当前版本并标注未解决的问题。
```

### 变体 3: 扇出工作流

```
Pass 1: 拆分任务
  ├─ Pass 2a: 处理子任务 1
  ├─ Pass 2b: 处理子任务 2
  └─ Pass 2c: 处理子任务 3
Pass 3: 合并结果
```

这种模式适合处理多个独立的子项目（如为多个 API 端点分别生成文档）。

Multi-Pass 是最基础也是最常用的工作流模式。但它不是唯一的选择。接下来我们介绍另外 4 种模式——它们来自对全球 5,400+ 个 Skill 的分析，每种模式都有独特的适用场景。

## 4.5 Pattern 2: 诊断-修复-验证 (Diagnose-Fix-Verify)

这个模式来自 OpenClaw 生态中的 `emergency-rescue` Skill——它用同一个三段式结构处理了 20+ 种 Git 灾难场景。

### 核心结构

```
诊断 (Diagnose) → 修复 (Fix) → 验证 (Verify)
   找出问题         解决问题        确认解决
```

每个场景都遵循完全相同的模板：

```markdown
### 场景：force-push 覆盖了 main 分支

# DIAGNOSE: 检查 reflog 确认发生了什么
git reflog show origin/main

# FIX: 恢复到正确的状态
git push origin <good-commit-hash>:main --force-with-lease

# VERIFY: 确认历史恢复正确
git log --oneline -10 origin/main
```

### 为什么这个模式有效

关键不在于三个步骤本身——而在于**验证步骤的存在**。没有 VERIFY，Agent 做完修复就认为任务完成了。但在真实场景中，修复可能没有生效、引入了新问题、或者解决了错误的根因。VERIFY 步骤强制 Agent 回头确认。

### 适用场景

- 排障类任务（Bug 修复、系统恢复、配置修复）
- 高风险操作（数据库修复、生产环境操作）
- 任何"先搞清楚发生了什么，再动手"的场景

### 设计要点

```markdown
## DIAGNOSE 部分的写法
- 列出具体的诊断命令（不要让 Agent 自己想）
- 每个命令注释说明它在检查什么
- 诊断结果应该可以推导出下一步行动

## FIX 部分的写法
- 使用最保守的修复方式（--force-with-lease 而非 --force）
- 破坏性操作标注 ⚠️
- 给出回退方案

## VERIFY 部分的写法
- 验证命令必须能确认修复是否成功
- 给出"成功"的预期输出
- 给出"失败"时的下一步指引
```

## 4.6 Pattern 3: 循环反馈 (Iterative Feedback Loop)

当任务质量无法一次到位时，你需要一个"做-评-改"的循环。这个模式来自 OpenClaw 的 `checkmate` Skill，它使用 Worker/Judge 架构来保证输出质量。

### 核心结构

```
执行 (Worker) → 评判 (Judge) → 通过? ──→ 输出
                                 ↓ 不通过
                            反馈差距 → 重试（最多 N 次）
```

### 案例：checkmate 的 Worker/Judge 架构

```markdown
## 工作流

### Step 1: Worker 执行任务
Worker 根据用户请求完成任务，产出初始结果。

### Step 2: Judge 评估质量
Judge 根据以下清单评估 Worker 的输出：
- [ ] 是否完全满足用户需求？
- [ ] 输出格式是否正确？
- [ ] 是否有逻辑错误？
- [ ] 是否遗漏了边界情况？

### Step 3: 反馈循环
如果 Judge 发现问题：
1. 精确描述差距（不是"不好"，而是"缺少错误处理"）
2. Worker 根据反馈修改
3. Judge 重新评估
4. 最多重复 10 次

### Step 4: 输出
Judge 评估通过后，输出最终结果。
```

### 与 Multi-Pass 循环变体的区别

Multi-Pass 的循环变体（4.4 变体 2）是**同一个角色**做执行和检查。而 Worker/Judge 模式在概念上把"做的人"和"评的人"分开——即使在同一个 Agent 中，这种分离也能显著提升输出质量，因为 Judge 会用更批判的视角审视 Worker 的输出。

### 适用场景

- 创意任务（写作、设计、方案规划）
- 质量要求高的输出（面向用户的文档、公开发布的内容）
- 需要多轮打磨的任务

## 4.7 Pattern 4: 条件分支 (Decision Tree)

有些 Skill 需要根据用户的意图或输入条件执行完全不同的逻辑。条件分支模式使用**意图解析表**来路由到正确的执行路径。

### 核心结构

```
用户输入 → 意图解析 → 路由到对应模式 → 执行
```

### 案例：anti-pattern-czar 的 5 种模式

`anti-pattern-czar` 是一个代码反模式检测 Skill，它根据用户说的关键词自动选择工作模式：

```markdown
## 意图解析

| User Says              | Mode   | Action                    |
|------------------------|--------|---------------------------|
| "scan", "detect"       | SCAN   | 运行检测器，保存状态       |
| "review", "fix"        | REVIEW | 交互式修复会话             |
| "auto", "fix all"      | AUTO   | 批量修复（带护栏）         |
| "resume", "continue"   | RESUME | 加载上次状态，继续工作     |
| "report", "status"     | REPORT | 展示当前检测状态           |

## SCAN 模式
1. 运行反模式检测器
2. 保存检测结果到 state.json
3. 输出摘要报告

## REVIEW 模式
1. 加载 state.json
2. 逐个展示问题，等待用户确认
3. 用户确认后自动修复
4. 更新 state.json

## AUTO 模式
1. 加载 state.json
2. 自动修复所有低风险问题
3. 高风险问题标记但不自动修复
4. 运行测试验证修复没有破坏功能
```

### 设计要点

- **意图解析表必须用表格**——不要用段落描述（回忆 3.8 的规则 2）
- **每种模式的指令独立**——可以单独阅读和执行
- **考虑状态恢复**——用户可能中途离开再回来（RESUME 模式）
- **默认模式**——如果无法判断意图，选择最安全的模式

### 适用场景

- 多功能 Skill（同一个 Skill 做扫描、修复、报告等）
- 用户交互复杂的 Skill
- 需要状态持久化的 Skill

## 4.8 Pattern 5: 量化决策 (Quantified Decision Matrix)

有些场景中，Agent 需要根据多个信号综合判断采取什么级别的行动。量化决策模式用打分矩阵替代模糊的"自行判断"。

### 核心结构

```
多个信号 → 加权打分 → 总分映射到行动级别
```

### 案例：adaptive-reasoning 的自适应推理

`adaptive-reasoning` Skill 根据任务复杂度自动调整推理深度：

```markdown
## 复杂度评估

| Signal              | Weight | Examples                    |
|---------------------|--------|-----------------------------|
| Multi-step logic    | +3     | 规划、证明、调试             |
| Ambiguity           | +2     | 有歧义的问题、权衡取舍       |
| Domain expertise    | +2     | 专业领域知识                 |
| Routine task        | -2     | 重复性工作、简单查询         |
| Clear instructions  | -1     | 用户已给出明确步骤           |

## 行动映射

| Score | Action                              |
|-------|-------------------------------------|
| <= 2  | 快速响应，无需额外推理              |
| 3-5   | 标准响应，简要分析                  |
| 6-7   | 深度分析，展示推理过程              |
| >= 8  | 启动扩展思考，多角度论证            |
```

### 为什么打分比"自行判断"好

当你写 "根据情况决定详细程度" 时，Agent 每次的判断标准可能不同。打分矩阵把隐性的判断过程变成了**显性的、可复现的**流程。即使某个信号的权重不完美，至少每次执行都遵循相同的逻辑。

### 适用场景

- 需要自适应行为的 Skill（调整详细程度、选择工具、分配资源）
- 风险评估（根据多个因素决定是否需要人工确认）
- 优先级排序（对多个待办事项进行加权排序）

## 4.9 模式选择指南

5 种模式不是互斥的——一个 Skill 可能同时使用多种模式。但选择**主模式**时，可以参考这个决策树：

```
你的任务需要多个阶段吗？
├─ 否 → 单步 Skill 就够了（第 3 章）
└─ 是 → 阶段之间是什么关系？
    ├─ 线性序列 → Pattern 1: Multi-Pass
    ├─ 出问题→修→验证 → Pattern 2: 诊断-修复-验证
    ├─ 做→评→改循环 → Pattern 3: 循环反馈
    ├─ 根据输入走不同路径 → Pattern 4: 条件分支
    └─ 根据多个信号自动决策 → Pattern 5: 量化决策
```

快速选择表：

| 任务特征 | 推荐模式 | 典型案例 |
|---------|---------|---------|
| 有确定步骤的线性任务 | Multi-Pass | API 文档生成、文章写作 |
| 排障和修复 | 诊断-修复-验证 | Git 灾难恢复、系统修复 |
| 质量需要多轮打磨 | 循环反馈 | 创意写作、方案设计 |
| 同一 Skill 多种功能 | 条件分支 | 多模式工具（扫描/修复/报告） |
| 需要自适应行为 | 量化决策 | 复杂度感知、风险评估 |

> **Tip**: 当你设计一个新 Skill 时，先问"这个任务最像上面哪种场景？"，然后从对应模式的模板开始写。模式的价值不在于限制你的创造力，而在于给你一个经过验证的起点。

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 复杂任务一步完成 | 用 5 种工作流模式拆解复杂任务 |
| 只知道 Multi-Pass | 掌握诊断-修复-验证、循环反馈、条件分支、量化决策 |
| 不知道选什么模式 | 用决策树和选择表快速匹配任务类型 |
| Agent 中途遗漏 | 交接文件和验证步骤确保信息不丢失 |

**Cumulative capability**: 你现在拥有 4 个 Skill（`quick-fix`、`code-review`、`commit-message`、`api-doc-writer`），并掌握了 5 种工作流设计模式。

## Try It Yourself

> 完整代码见 `code/track-1/ch04-api-doc-writer/`，可直接复制到 `~/.qoder/skills/` 使用。
>
> **Track 2 演进**：对比 `code/track-2/v03-five-elements/` 和 `code/track-2/v04-multi-pass/` 的 diff，
> 观察 3-Pass 工作流和暂停点如何将 38 行扩展为 89 行。

1. **Verify**: 用 `api-doc-writer` 为一个真实 API 项目（或小型示例项目）生成文档。观察三个 Pass 的执行过程。

2. **Extend**: 把 Chapter 3 的 `commit-message` 改写成 2-Pass 版本——Pass 1 分析 diff 并输出改动摘要，Pass 2 基于摘要生成提交信息。对比单步版本，质量是否提升？

3. **Explore**: 想一个你工作中的复杂流程（如代码 review、release 准备、新员工 onboarding 文档）。画出它的 Multi-Pass 流程图，标出每个 Pass 的输入、输出和暂停点。

4. **Design**: 为一个 Bug 修复 Skill 选择"诊断-修复-验证"模式，写出 DIAGNOSE/FIX/VERIFY 三段的完整指令。然后设想 3 种不同的 Bug 场景，验证你的模板是否通用。

## Summary

- **Multi-Pass** 把复杂任务拆成多个阶段，每个阶段只做一件事
- **诊断-修复-验证**适用于排障场景——验证步骤是关键
- **循环反馈**的 Worker/Judge 分离打破了自我评估的盲点
- **条件分支**用意图解析表路由到不同执行路径
- **量化决策**用打分矩阵替代模糊的"自行判断"
- 用**模式选择决策树**快速匹配任务类型到合适的工作流模式
- Pass 之间通过**交接文件**传递信息，不依赖 Agent 记忆
- 一个 Skill 可以混合使用多种模式

## Further Reading

- 编译器管线设计：Lexer → Parser → AST → IR → CodeGen（Multi-Pass 的经典灵感来源）
- Unix 管道哲学："一个程序只做一件事，做好它"——Skill 的每个 Pass 也应如此
- 第 5 章《命令与路由》——让每个 Pass 可以单独执行
- OpenClaw `emergency-rescue` Skill——诊断-修复-验证模式的典范
- OpenClaw `checkmate` Skill——Worker/Judge 循环反馈的实现
