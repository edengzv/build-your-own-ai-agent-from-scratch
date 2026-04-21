# Chapter 10: 测试与调优

> **Motto**: "写完不是终点，验证才是"

> 你已经掌握了写 Skill 的全部技巧。但一个 Skill 写出来后，怎么知道它好不好？怎么持续改进？本章教你建立 Skill 的评估方法论：设计测试用例、对比 A/B 版本、收集反馈、持续迭代。

![Chapter 10: 测试与调优](images/ch10-testing-tuning.png)

## The Problem

你写了 `commit-message` Skill 的两个版本：

- v1：简单的步骤 + 约束
- v2：增加了示例 + 输出模板

你"觉得" v2 更好——但你不确定。是真的更好还是只是更长？在什么情况下 v2 更好？有没有 v1 反而更好的场景？

没有系统性的测试，你只能靠"感觉"。

## The Solution

对 Skill 的系统性评估包含四个维度和一个迭代循环。

## 10.1 Skill 的四个质量维度

| 维度 | 定义 | 测试方法 |
|------|------|---------|
| **触发准确性** | 该加载时加载，不该时不加载 | 用不同请求测试加载率 |
| **执行一致性** | 同样输入，输出质量稳定 | 同一请求运行 5 次，对比输出 |
| **输出质量** | 满足预期效果 | 人工评估 + Checklist 通过率 |
| **Token 效率** | 用最少 tokens 达到效果 | 测量 SKILL.md 大小 vs 效果 |

### 触发准确性测试

设计 10 个请求，5 个应该触发 Skill，5 个不应该：

```markdown
## 触发测试用例 — commit-message Skill

应该触发（期望加载）：
1. "帮我写 commit message"
2. "生成提交信息"
3. "这些改动应该怎么提交"
4. "write a commit message for these changes"
5. "我要提交代码了"

不应该触发（期望不加载）：
6. "帮我审查代码" → 应触发 code-review
7. "读一下 git log"
8. "这段代码有 Bug"
9. "创建一个新文件"
10. "解释什么是 Git rebase"
```

测试每个请求，记录是否正确触发。目标：**10/10 正确**。

### 执行一致性测试

同一个请求运行 5 次，对比输出：

```
请求："为当前 staged changes 生成 commit message"
（确保 staged changes 一样）

Run 1: fix(auth): correct token expiration check     ✓ 格式正确
Run 2: fix(auth): fix JWT expiration comparison       ✓ 格式正确
Run 3: Fixed the token bug in auth middleware         ✗ 没用 Conventional Commits
Run 4: fix(auth): resolve timestamp mismatch in JWT   ✓ 格式正确
Run 5: fix(auth): multiply exp by 1000 for ms check  ✓ 格式正确

一致性：4/5 = 80%
```

如果一致性低于 80%，需要加强指令或示例。

### 输出质量评估

对每次输出，按 Skill 的 Quality Checklist 评分：

```
Run 1: 6/6 checklist items passed → 100%
Run 2: 5/6 (title too long) → 83%
Run 3: 3/6 (wrong format, no type, no scope) → 50%
Run 4: 6/6 → 100%
Run 5: 6/6 → 100%

平均质量：86.6%
```

## 10.2 断言分类体系

上面的质量评估是人工打分的。但有些维度可以**自动化验证**——用断言（assertion）。

断言是对 Skill 输出的可编程检查。工具 Promptfoo 提供了一套成熟的断言分类体系，分为三个层次：

### Layer 1: 确定性断言

这些断言有确定的对/错，不需要 LLM 判断：

| 断言类型 | 检查内容 | 示例 |
|---------|---------|------|
| `contains` | 输出包含指定字符串 | 输出必须包含 `fix(` 或 `feat(` |
| `not-contains` | 输出不包含指定字符串 | 输出不能包含 `TODO` |
| `is-json` | 输出是合法 JSON | API 响应格式检查 |
| `regex` | 输出匹配正则表达式 | `/^(feat|fix|refactor)\(.+\):/` |
| `equals` | 输出精确匹配 | 特定配置值 |
| `max-length` | 输出不超过指定长度 | 标题行 <= 50 字符 |

确定性断言适合检查**格式**——格式要么对要么错，没有灰色地带。

### Layer 2: 轨迹断言

这些断言检查的不是输出内容，而是**执行过程**：

| 断言类型 | 检查内容 | 示例 |
|---------|---------|------|
| `tool-used` | Agent 是否使用了指定工具 | 必须调用了 `git diff --cached` |
| `tool-not-used` | Agent 是否避免了某工具 | 不应该执行 `git push` |
| `tool-sequence` | 工具调用顺序是否正确 | 先 `Read` 再 `Edit`（不是先编辑再读） |
| `step-count` | 执行步骤数在范围内 | 不超过 10 步 |

轨迹断言适合检查**行为**——Agent 是否按预期的工作流执行。

### Layer 3: 模型辅助断言

当"对/错"不是非黑即白时，用另一个 LLM 来判断：

| 断言类型 | 检查内容 | 示例 |
|---------|---------|------|
| `llm-rubric` | 输出是否满足自然语言描述的标准 | "commit message 是否解释了 why" |
| `factuality` | 输出是否包含事实错误 | 和源代码对比，检查参数描述是否准确 |
| `similarity` | 输出和参考答案的语义相似度 | 和人工写的 gold standard 对比 |

模型辅助断言适合检查**语义质量**——需要"判断力"的维度。

### 混合使用策略

实际的 Skill 测试通常混合三个层次：

```
commit-message Skill 的断言集:

确定性:
  - regex: /^(feat|fix|refactor|docs|test|chore)\(.+\):/  # Conventional Commits 格式
  - max-length: title <= 50 chars                           # 标题长度
  - not-contains: "."  (in title line)                      # 标题不以句号结尾

轨迹:
  - tool-used: git diff --cached                            # 必须分析 staged changes
  - tool-not-used: git push                                 # 不应该自动 push

模型辅助:
  - llm-rubric: "body 解释的是 WHY 而不是 WHAT"              # 语义质量
  - llm-rubric: "使用祈使语气（add, fix, not added, fixed）"  # 风格
```

> **Tip**: 先写确定性断言（成本为零），再加轨迹断言（需要日志），最后按需加模型辅助断言（每次运行消耗 tokens）。

## 10.3 A/B 版本对比

当你改进 Skill 时，保留旧版本做对比：

```
skills/
├── commit-message/        ← 当前版本 (v2)
│   └── SKILL.md
└── commit-message-v1/     ← 对比版本 (v1)
    └── SKILL.md
```

用**同一组测试用例**分别测试两个版本，对比四个维度的得分。

### A/B 实验记录模板

```markdown
## Experiment: commit-message v1 vs v2

### 变更项
v1: 步骤 + 约束（50 行）
v2: 步骤 + 约束 + 2 个示例 + 输出模板（90 行）

### 测试用例
[5 个相同的测试请求]

### 结果

| 维度 | v1 | v2 |
|------|-----|-----|
| 触发准确性 | 8/10 | 9/10 |
| 执行一致性 | 60% | 85% |
| 输出质量（avg） | 72% | 91% |
| Token 消耗 | 500 | 900 |

### 结论
v2 在一致性和质量上显著提升（+25%, +19%），代价是多消耗 400 tokens。
考虑到上下文窗口的预算，这个 trade-off 是值得的。
采纳 v2。
```

## 10.4 Description 自动化优化循环

在第 2 章，我们预告了 Anthropic 的 description 自动化优化方法。现在完整展开。

### 为什么需要自动化

手动测试 description 的问题：你只能想到有限的测试查询，而且你的"直觉"会过拟合到你自己的使用习惯。自动化优化循环解决了这两个问题。

### 完整流程

**Step 1: 生成触发评估查询**

为你的 Skill 创建 20 个评估查询——10 个 should-trigger（应该触发），10 个 should-not-trigger（不应触发）：

```json
[
  {"query": "ok so my boss just sent me this xlsx file and I need to pull out the Q3 numbers", "should_trigger": true},
  {"query": "can you help me analyze this CSV data in pandas", "should_trigger": false},
  {"query": "I have a spreadsheet with employee data that needs cleaning up", "should_trigger": true},
  {"query": "write me a python script to parse Excel files", "should_trigger": false}
]
```

关键要求：
- 查询必须**真实且具体**（包含细节、背景、口语化表达）
- should-not-trigger 查询必须是**近似误匹配**——和 Skill 相关但不应触发
- 避免过于简单的查询——简单查询不会触发任何 Skill，测试它们没意义

**Step 2: 分割训练/测试集**

按 **60/40** 比例分割：12 个训练查询 + 8 个测试查询。训练集用于发现问题和改进 description；测试集只在最后用于选择最佳版本。

为什么不用全部 20 个？防止**过拟合**——如果你根据所有查询调整 description，你的改进可能只适用于这些特定查询，而非真实使用场景。

**Step 3: 评估当前 description**

对训练集的每个查询运行 **3 次**（因为 LLM 的触发判断有随机性），记录触发率：

```
query_01 (should_trigger=true):  3/3 triggered  → PASS
query_02 (should_trigger=true):  2/3 triggered  → WEAK PASS
query_03 (should_trigger=false): 0/3 triggered  → PASS
query_04 (should_trigger=false): 2/3 triggered  → FAIL
...
训练集准确率: 75%
```

**Step 4: 分析失败案例，改进 description**

对每个 FAIL 和 WEAK PASS，分析原因：
- should-trigger 但没触发？→ description 缺少关键词或场景描述
- should-not-trigger 但触发了？→ description 太宽泛，需要加限定词

基于分析修改 description，然后回到 Step 3。

**Step 5: 选择最佳版本**

最多迭代 **5 轮**。每轮结束后，在**测试集**上评估当前 description：

```
Iteration 1: train=75%, test=70%
Iteration 2: train=83%, test=78%
Iteration 3: train=92%, test=82%
Iteration 4: train=95%, test=80%  ← 测试集下降，可能过拟合
Iteration 5: train=98%, test=79%  ← 继续下降

最佳版本: Iteration 3（测试集最高）
```

**按测试集分数选最佳版本**——即使训练集分数继续上升，测试集下降意味着你在过拟合。

### 何时值得做

这个流程每次需要 60+ 次 Skill 加载测试。对于个人使用的 Skill 可能不值得。但对于以下场景值得投入：

- 团队共享的 Skill（被多人使用）
- 发布到社区的 Skill
- 触发率问题严重影响使用体验的 Skill

## 10.5 四维诊断：精准定位改进方向

当 Skill 表现不佳时，第一步是定位问题属于**哪个维度**。简单的排除法有时不够——SkillForge 项目提出了一个更系统的四维诊断框架：

### 四个诊断维度

| 维度 | 核心问题 | 典型症状 | 改进方向 |
|------|---------|---------|---------|
| **知识** | Skill 知道的够吗？ | 输出包含事实错误、遗漏关键信息 | 补充 references/、增加背景知识 |
| **工具使用** | 工具编排正确吗？ | 用错工具、调用顺序错误、遗漏必要的工具调用 | 修正步骤序列、添加轨迹断言 |
| **澄清策略** | 该问用户时问了吗？ | 在关键决策点自行假设、不该问时却反复确认 | 调整暂停点设计（Ch4） |
| **语气/风格** | 输出风格合适吗？ | 过于冗长、过于简短、语气不匹配场景 | 调整示例和输出模板（Ch6） |

### 诊断决策树

```
Skill 输出有问题
│
├─ 没有被加载？
│  └─ description 问题 → 回到 Ch2 / 10.4 优化循环
│
├─ 加载了，但输出不对
│  │
│  ├─ 事实/内容错误？ → 知识维度
│  │  检查：Skill 是否缺少必要的领域知识？
│  │  修复：补充 references/ 或在指令中添加上下文
│  │
│  ├─ 执行过程错误？ → 工具使用维度
│  │  检查：Agent 是否按预期顺序使用了正确的工具？
│  │  修复：修正步骤序列，添加工具约束
│  │
│  ├─ 不该自行决定的事自己决定了？ → 澄清策略维度
│  │  检查：关键决策点是否设置了暂停？
│  │  修复：添加暂停点，明确"何时该问用户"
│  │
│  └─ 内容对但"感觉不对"？ → 语气/风格维度
│     检查：输出的详细程度、语气是否匹配场景？
│     修复：调整示例、输出模板、角色声明
```

### 改进优先级

四个维度的改进有不同的 ROI（投入产出比）：

- **知识修复**：效果立竿见影，但**很快饱和**——该补的知识补完后，继续补也不会更好
- **工具使用修复**：效果持续，每一次改进都能稳定提升
- **澄清策略修复**：效果依赖场景，但显著提升用户满意度
- **风格修复**：效果持续，不断微调可以越来越好

这个发现来自 SkillForge 项目的大规模实验——它意味着你的改进策略应该是：先快速修复知识缺口，然后把精力放在工具编排和风格调优上。

## 10.6 何时停止迭代：知识饱和曲线

一个常见的陷阱：你不断改进 Skill，但感觉到了某个点之后进步越来越小。这不是你的错——这是**知识饱和**现象。

### 饱和曲线模型

```
质量
  │     知识修复         工具+风格修复
  │      ┌─────┐          ┌──────
  │     /       \        /
  │    /         ----   /
  │   /              \ /
  │  /                ×  ← 饱和点
  │ /
  │/
  └──────────────────────────────→ 迭代次数
```

SkillForge 发现：
- **知识类改进**在 2-3 轮后就趋于饱和——该给的知识给了，再给也不会更好
- **工具使用改进**和**风格改进**可以持续多轮，每轮都有边际收益

### 实践指导

当你发现以下信号时，说明知识维度已饱和：
- 补充了新的 references，但输出质量没有变化
- 增加了更多示例，但 Agent 没有利用它们
- 知识类断言全部通过，但用户仍不满意

此时应该**转向**：
- 优化工具编排（步骤序列的顺序、分支条件）
- 微调输出风格（详细程度、语气、格式）
- 改进澄清策略（何时问用户、问什么）

> **Tip**: 如果连续 2 轮迭代在同一个维度上都没有改善，换一个维度。

## 10.7 版本管理

用 Git 管理 Skill 的演进：

```bash
cd ~/.qoder/skills/commit-message
git init
git add SKILL.md
git commit -m "v1: basic commit message skill"

# 改进后
git add SKILL.md
git commit -m "v2: add examples and output template"
```

每次重大改进后打 tag：

```bash
git tag v1.0 -m "Initial release"
git tag v2.0 -m "Add examples, +25% consistency"
```

如果新版本不如旧版本，直接回滚：

```bash
git checkout v1.0 -- SKILL.md
```

## 10.8 持续迭代循环

```
     ┌──────────┐
     │ 收集问题  │ ← 使用中发现的不满意之处
     └─────┬────┘
           ↓
     ┌──────────┐
     │ 四维诊断  │ ← 知识/工具/澄清/风格
     └─────┬────┘
           ↓
     ┌──────────┐
     │ 修改 Skill│ ← 针对性修复（注意饱和点）
     └─────┬────┘
           ↓
     ┌──────────┐
     │ A/B 测试  │ ← 断言 + 人工评估
     └─────┬────┘
           ↓
     ┌──────────┐
     │ 部署/回滚 │ ← 数据说了算
     └─────┬────┘
           │
           └──→ 回到"收集问题"
```

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 靠感觉判断 Skill 好坏 | 四维度量化评估 + 三层断言体系 |
| 改进后不知道是否真的更好 | A/B 对比 + 断言自动化验证 |
| 问题无从下手 | 四维诊断精准定位（知识/工具/澄清/风格） |
| 不知道什么时候该停止改进 | 知识饱和曲线指导迭代策略 |
| description 只能手动优化 | 自动化 description 优化循环（60/40 + 5 轮迭代） |

**Cumulative capability**: 你现在能系统性地测试和迭代你的 Skill，有数据支撑每一次改进决策。掌握了断言分类体系、四维诊断和知识饱和曲线。

## Try It Yourself

> 本章的实践材料见 `code/track-1/ch10-eval/`，包含 eval-config.yaml 模板、测试用例集和 description 优化日志模板。
>
> **Track 2 演进**：对比 `code/track-2/v09-quality/` 和 `code/track-2/v10-eval/` 的 diff，
> 观察 Pass 4（评测建议）和 run_eval.sh 如何从 321 行扩展到 437 行。

1. **Verify**: 对你的 `commit-message` Skill 做一次完整的四维度评估。记录触发准确性、一致性、质量和 Token 消耗。
2. **Assertions**: 为 `commit-message` Skill 设计 5 个确定性断言和 2 个模型辅助断言。手动运行并记录结果。
3. **4D Diagnosis**: 选一个你觉得"不够好"的 Skill，用四维诊断框架分析问题属于哪个维度，然后做针对性改进。
4. **Optimization Loop**: 如果你有一个触发率不理想的 Skill，尝试 description 优化循环的前 3 步（生成查询、分割训练/测试、评估）。

## Summary

- 四个质量维度：**触发准确性、执行一致性、输出质量、Token 效率**
- **三层断言体系**：确定性（格式）→ 轨迹（行为）→ 模型辅助（语义）
- **A/B 对比**是验证改进是否有效的最可靠方法
- **Description 优化循环**：20 查询 → 60/40 分割 → 3 次运行 → 按测试集选最佳
- **四维诊断**：知识 / 工具使用 / 澄清策略 / 语气风格
- **知识饱和曲线**：知识修复很快饱和，工具和风格修复可持续改进
- 用 **Git** 管理 Skill 版本，支持回滚
- 迭代循环：收集问题 → 四维诊断 → 修改 → 测试 → 部署

## Further Reading

- Promptfoo 文档——断言分类体系的完整参考
- A/B 测试的统计学基础：如何判断两个版本的差异是否显著
- 第 2 章回顾：description 是最常需要调优的部分
- 第 11 章《案例解剖》——看看优秀 Skill 是如何迭代演进的
- SkillForge (Yang et al.) — 四维诊断和知识饱和曲线的学术论文
