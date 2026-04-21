# Skill 创建与优化工具生态调研：Anthropic Skill-Creator 的竞品与互补方案

> 调研时间：2026-04-19
> 数据来源：GitHub 仓库、arXiv 论文、官方文档、技术博客
> 关联章节：Ch10（测试与调优）、Ch12（元技能）
> 前置阅读：anthropic-skill-creator-research.md

---

## 一、调研背景

Anthropic 的 skill-creator 是目前最成熟的**人机协作式** Skill 创建工具。但市场上还存在多个不同路径的方案——从程序化优化框架到学术界的自主进化系统。本报告梳理这些方案，提取对我们 Skill 书有价值的最佳实践。

### 方案分类矩阵

```
                     手动 ←──── 自动化程度 ────→ 全自动
                      │                            │
  LangGPT ────────────┤                            │
  Anthropic Skill-Creator ──────┤                  │
  Skill-Tester ─────────────────┤                  │
  Promptfoo ────────────────────────┤              │
  DSPy / Skill-Optimizer ──────────────────┤       │
  EvoSkill ────────────────────────────────────┤   │
  EvoSkills ───────────────────────────────────────┤
  SkillForge ──────────────────────────────────────┤
```

---

## 二、各方案详解

### 2.1 LangGPT — 结构化 Prompt 模板框架

| 属性 | 内容 |
|------|------|
| 仓库 | github.com/langgptai/LangGPT |
| 论文 | arxiv.org/abs/2402.16929（2024） |
| Stars | 5,000+ |
| 定位 | 结构化 Prompt 设计框架，类似 "Prompt 的编程语言" |

#### 核心思想

LangGPT 将 Prompt 设计类比为编程，提出了标准化的 Prompt 模板结构：

```markdown
# Role: 角色名

## Profile
- author: 作者
- version: 版本
- language: 语言
- description: 描述

## Goals
- 目标1
- 目标2

## Skills
- 技能1
- 技能2

## Constraints
- 约束1
- 约束2

## Workflows
1. 步骤1
2. 步骤2

## Init
初始化行为
```

#### 关键特性

- **模块化设计**：每个部分（Role, Skills, Constraints）像代码模块一样独立、可复用
- **变量替换**：使用 `<placeholder>` 语法实现动态参数化
- **斜杠命令**：定义 `/command` 快捷操作
- **记忆增强**：通过结构化格式减少对话漂移
- **学术支撑**：有正式论文验证其有效性

#### 对我们书的启示

| 启示 | 可借鉴到 |
|------|---------|
| 结构化模板比自由格式 Prompt 更稳定 | Ch03 可执行指令 |
| Role + Skills + Constraints 的三元组 | Ch03 结构化指令五要素 |
| 变量占位符实现 Prompt 复用 | Ch06 模板与示例 |
| 与 SKILL.md 的 Frontmatter + Body 模式高度一致 | Ch01 Skill 基础 |

#### 局限性

- 纯模板方案，没有测试和迭代机制
- 不涉及触发/路由问题（没有 description 优化）
- 与 Agent Skill 生态没有直接整合

---

### 2.2 DSPy — 程序化 Prompt 优化框架

| 属性 | 内容 |
|------|------|
| 官网 | dspy.ai |
| 作者 | Stanford NLP (Omar Khattab 等) |
| Stars | 25,000+ |
| 定位 | 声明式 LLM 编程框架，用程序替代手写 Prompt |

#### 核心思想

DSPy 的哲学是：**不要手写 Prompt，而是声明意图，让优化器自动找到最佳 Prompt。**

```python
# 声明模块（意图）
class RAG(dspy.Module):
    def __init__(self):
        self.retrieve = dspy.Retrieve(k=3)
        self.generate = dspy.ChainOfThought("context, question -> answer")
    
    def forward(self, question):
        context = self.retrieve(question).passages
        return self.generate(context=context, question=question)

# 用优化器自动寻找最佳 prompt
optimizer = dspy.MIPROv2(metric=my_metric, num_threads=8)
optimized_rag = optimizer.compile(RAG(), trainset=train_data)
```

#### 优化器家族

| 优化器 | 原理 | 优化目标 |
|--------|------|---------|
| **MIPROv2** | 贝叶斯优化 | 指令 + Few-shot 示例联合优化 |
| **BootstrapFewShot** | 自动生成示例 | Few-shot 示例选择 |
| **COPRO** | 坐标上升 | 指令文本优化 |
| **BootstrapFewShotWithRandomSearch** | 随机搜索 | 示例组合 |
| **SIMBA** | 分片搜索 | 大规模程序优化 |

#### 关键特性

- **声明式编程**：`dspy.Signature("question -> answer")` 替代手写 Prompt
- **自动编译**：Optimizer 基于训练数据自动优化指令和示例
- **度量驱动**：所有优化基于用户定义的度量函数（metric）
- **模型无关**：优化出的 Prompt 可跨模型迁移

#### 对我们书的启示

| 启示 | 可借鉴到 |
|------|---------|
| 度量函数（metric）是优化的前提——不能度量就不能优化 | Ch10 测试与调优 |
| 指令和示例应该联合优化，而非分开调整 | Ch06 模板与示例 |
| 贝叶斯优化比人工 A/B 测试更高效 | Ch10 A/B 对比 |
| 训练集/测试集分割防止过拟合 | Ch10（与 Anthropic description optimization 一致） |

#### 局限性

- 需要编程能力，门槛高于 SKILL.md
- 需要标注数据（训练集）
- 优化的是原子 Prompt，不直接产出 SKILL.md 格式的知识包

---

### 2.3 Skill-Optimizer — DSPy + Agent Skills 的桥梁

| 属性 | 内容 |
|------|------|
| 仓库 | github.com/Ash-Blanc/skill-optimizer |
| 定位 | 用 DSPy 优化 Agent Skill 的指令和示例 |

#### 核心思想

将 DSPy 的优化能力直接应用于 YAML/Markdown 格式的 Skill 定义：

1. 用户定义 Skill（YAML 或 Markdown）
2. 系统评估基线性能
3. 自动生成合成训练数据
4. 用 MIPROv2/BootstrapFewShot/COPRO 等算法优化指令和示例
5. 展示优化前后对比

#### 关键特性

- **预优化分析**：评估 Skill 的改进潜力
- **多算法支持**：自动选择最适合的优化策略
- **合成数据生成**：不需要手工标注，自动创建训练样本
- **与 Agno 集成**：支持持久记忆和动态 Few-shot 检索

#### 对我们书的启示

| 启示 | 可借鉴到 |
|------|---------|
| 合成数据可以降低测试成本 | Ch10 测试用例设计 |
| 优化前先评估改进潜力，避免无效优化 | Ch10 质量维度 |
| 将 DSPy 优化器作为 Skill 改进的自动化后端 | Ch12 元技能 |

---

### 2.4 Promptfoo — 通用 LLM 评估框架

| 属性 | 内容 |
|------|------|
| 仓库 | github.com/promptfoo/promptfoo |
| Stars | 6,000+ |
| 定位 | CLI + 库，用于评估、对比和红队测试 LLM 应用 |

#### 核心思想

用**声明式配置**定义测试用例和断言，自动运行评估并生成对比报告：

```yaml
prompts:
  - "Summarize: {{text}}"
  - "TL;DR: {{text}}"

providers:
  - openai:gpt-4
  - anthropic:claude-3

tests:
  - vars:
      text: "Long article..."
    assert:
      - type: contains
        value: "key point"
      - type: llm-rubric
        value: "Summary is concise and accurate"
      - type: cost
        threshold: 0.01
```

#### 断言类型体系（最有价值的部分）

Promptfoo 定义了迄今最完整的 LLM 输出验证分类体系：

**确定性断言（Deterministic）**：
| 类别 | 断言类型 |
|------|---------|
| 字符串匹配 | `equals`, `contains`, `starts-with`, `contains-any`, `contains-all` |
| 结构验证 | `is-json`, `contains-json`, `is-html`, `is-xml`, `is-sql` |
| 函数调用验证 | `is-valid-function-call`, `is-valid-openai-tools-call` |
| 安全/拒绝 | `is-refusal`, `guardrails` |
| 度量阈值 | `rouge-n`, `bleu`, `levenshtein`, `latency`, `cost` |
| 自定义 | `javascript`, `python`, `webhook` |

**Agent/Skill 专用断言**：
| 断言类型 | 说明 |
|---------|------|
| `skill-used` | 验证是否使用了特定 Skill |
| `trajectory:tool-used` | 验证是否调用了特定工具 |
| `trajectory:tool-args-match` | 验证工具调用参数是否匹配 |
| `trajectory:tool-sequence` | 验证工具调用顺序 |
| `trajectory:step-count` | 验证执行步骤数 |
| `trajectory:goal-success` | 验证是否达成目标 |

**模型辅助断言（Model-Assisted）**：
| 断言类型 | 说明 |
|---------|------|
| `llm-rubric` | 用 LLM 按评分标准评估 |
| `factuality` | 事实性验证 |
| `answer-relevance` | 答案相关性 |
| `context-faithfulness` | 上下文忠实度 |
| `similar` | 语义相似度 |

**高级特性**：
- 加权断言：不同断言不同权重
- 断言组（assert-set）：一组断言达到阈值即通过
- 派生度量：`weighted_score = accuracy * 0.6 + relevance * 0.4`

#### 对我们书的启示

| 启示 | 可借鉴到 |
|------|---------|
| **断言分类体系**是最大价值——可直接借用到 Skill 测试 | Ch10 测试用例设计 |
| `trajectory:*` 断言特别适合验证 Skill 的工具编排行为 | Ch08 多工具编排 |
| `skill-used` 断言可以验证 description 触发准确性 | Ch02 Description |
| 加权断言 + 阈值模式比简单 pass/fail 更实用 | Ch09 质量检查 |
| 声明式 YAML 配置比脚本更易维护 | Ch10 测试框架设计 |
| 本地运行、隐私优先的设计哲学 | 通用原则 |

#### 与 Anthropic Skill-Creator 的互补

Anthropic skill-creator 的评估系统是定制的（grading.json + benchmark.json + eval-viewer），而 promptfoo 提供了更通用、更丰富的断言体系。两者可以互补：

- Skill-creator 擅长：人机协作的定性反馈循环
- Promptfoo 擅长：自动化的定量断言和回归测试

---

### 2.5 Skill-Tester — 技能质量门禁

| 属性 | 内容 |
|------|------|
| 仓库 | github.com/alirezarezvani/claude-skills |
| 定位 | Skill 仓库的自动化质量检查工具 |

#### 核心架构

三个 Python 模块组成质量检查管线：

```
skill_validator.py  →  script_tester.py  →  quality_scorer.py
  结构与文档验证         运行时测试执行         多维度质量评分
```

#### 评分维度

| 维度 | 权重 | 检查内容 |
|------|------|---------|
| 文档质量 | 25% | SKILL.md 格式、元数据完整性、描述质量 |
| 代码健壮性 | 25% | 语法正确性、标准库限制、参数解析 |
| 资源完整性 | 25% | 目录结构、引用文件存在性 |
| 用户体验 | 25% | 错误消息、输出格式、边界处理 |

#### 集成方式

- **Pre-commit Hook**：提交前自动验证
- **CI/CD**：PR 中自动检查 Skill 质量
- **批量扫描**：对整个 Skill 目录生成质量统计

#### 对我们书的启示

| 启示 | 可借鉴到 |
|------|---------|
| 质量检查应该自动化，而非依赖人工 review | Ch09 质量检查 |
| 多维度加权评分比单一 pass/fail 更有区分度 | Ch09 评分系统 |
| Pre-commit 集成确保质量门禁不被跳过 | Ch10 版本管理 |
| 复杂度分级（basic → powerful）帮助设定期望 | Ch01 Skill 分类 |

---

### 2.6 EvoSkill — 失败驱动的自动 Skill 发现

| 属性 | 内容 |
|------|------|
| 仓库 | github.com/sentient-agi/EvoSkill |
| 论文 | arxiv.org/abs/2603.02766（2025-03） |
| Stars | 509 |
| 定位 | 从失败轨迹中自动发现和合成可复用 Agent Skill |

#### 核心思想

**不需要人来设计 Skill——从 Agent 的失败中自动提炼。**

```
Phase 1: Baseline Agent 尝试解决问题
Phase 2: Reviewer 分析失败原因
Phase 3: Writer 提出 Skill/Prompt 修改
Phase 4: Scorer 用 held-out 数据验证
Phase 5: Tracker 用 Git 分支管理最优版本
```

#### 关键特性

- **失败轨迹分析**：不是从成功案例学习，而是从失败中提取教训
- **GEPA/DSPy 风格优化**：自动发现弱点、起草修改、验证、保留优胜者
- **Skill Library**：产出的 Skill 存为模块化目录，兼容 `.claude/skills/` 格式
- **跨任务迁移**：在一个任务上发现的 Skill 可以提升其他任务（如 SealQA Skill 提升 BrowseComp 表现）

#### 实验结果

- 准确率从 42.0% 提升到 51.3%（两轮进化）
- 证明了跨任务迁移性

#### 对我们书的启示

| 启示 | 可借鉴到 |
|------|---------|
| **失败分析是 Skill 创建的重要信号源** | Ch10 迭代循环 |
| Skill 应该能跨任务复用——验证其泛化能力 | Ch10 测试设计 |
| Git 分支管理 Skill 版本进化 | Ch10 版本管理 |
| 自动化发现 vs 人工设计是两种互补路径 | Ch12 元技能 |

---

### 2.7 EvoSkills — 生成器-验证器协同进化

| 属性 | 内容 |
|------|------|
| 官网 | evoskills.net |
| 论文 | arxiv.org/html/2604.01687v1（2026-04） |
| 定位 | 无需真实标注数据的 Skill 自主进化 |

#### 核心创新：打破自我验证的确认偏误

EvoSkills 的核心突破是**信息隔离**：

```
┌──────────────────┐      ┌──────────────────┐
│   Generator      │      │   Verifier       │
│                  │      │                  │
│ 生成/改进 Skill  │ ←──→ │ 独立评估+诊断    │
│ 保留历史评估数据 │      │ 生成合成测试断言  │
│                  │      │ 产出结构化失败报告│
└──────────────────┘      └──────────────────┘
      ↑                          ↑
      └── 信息隔离：互不知道对方的内部状态 ──┘
```

#### 与 EvoSkill（单 l）的关键区别

| 维度 | EvoSkill | EvoSkills |
|------|----------|-----------|
| 反馈来源 | 真实标注数据 | 合成测试断言（无需标注） |
| 架构 | 单管线 | Generator-Verifier 双向协同 |
| 反馈粒度 | 按任务级别 | 按断言级别（更精细） |
| 输出格式 | 结构化目录 | 集成 Skill 包 |
| 迁移验证 | 跨任务 | 跨模型 |

#### 实验结果

- 性能从 32% → 75%（5 轮进化）
- 超越人工编写的 Skill（71.1% vs 53.5%）
- 跨模型迁移提升 +35 到 +44 个百分点

#### 对我们书的启示

| 启示 | 可借鉴到 |
|------|---------|
| **确认偏误是自检的最大敌人**——生成者和验证者必须隔离 | Ch09 质量检查 |
| 合成测试断言可以替代人工标注 | Ch10 测试用例 |
| 按断言级别（而非任务级别）提供反馈更精确 | Ch09 检查清单 |
| 5 轮进化即可超越人工 Skill——说明迭代本身比初始质量更重要 | Ch10 迭代循环 |

---

### 2.8 SkillForge — 领域特定 Skill 的自动锻造

| 属性 | 内容 |
|------|------|
| 论文 | arxiv.org/html/2604.08618v1（2026-04） |
| 定位 | 从企业工单和文档中自动生成并持续进化领域 Skill |

#### 核心架构

```
┌─────────────────────────────────────┐
│   Domain-Contextualized Skill Creator   │
│   从历史工单和文档挖掘分辨率工作流        │
│   提取工具 Schema 和参考材料              │
│   合成为结构化 Skill 包                   │
└───────────────┬─────────────────────┘
                │
                ↓ 持续进化循环
┌───────────────────────────────────────┐
│ Failure Analyzer → Skill Diagnostician → Skill Optimizer │
│                                                           │
│ LLM-Judge 评估     并行分析4个维度      证据驱动的         │
│ 响应 vs 专家参考   (知识/工具/澄清/语气)  定向修改          │
│                                                           │
│        所有修改在沙盒 VFS 中执行（安全 + 版本追踪）         │
└───────────────────────────────────────┘
```

#### 关键创新

1. **领域感知初始化**：从企业历史数据（工单、文档）中提取 Skill，而非从零开始
2. **四维并行诊断**：对失败响应同时从知识、工具使用、澄清策略、语气四个维度分析
3. **沙盒虚拟文件系统（VFS）**：所有 Skill 修改在安全隔离环境中进行
4. **证据驱动修改**：每次修改都必须有具体证据支撑，精准映射到 Skill 的具体段落

#### 实验结果

- 在 1,883 个真实工单上评估
- 3 轮进化后超越成熟的人工编写生产系统 13+ 个百分点
- 关键发现：知识类修复通常很快饱和（收益递减），而工具和风格类修复可以持续改进

#### 对我们书的启示

| 启示 | 可借鉴到 |
|------|---------|
| **从企业数据初始化 Skill**比从空白开始效率高得多 | Ch12 元技能 |
| **四维诊断**框架可用于人工 Skill 改进 | Ch10 迭代循环 |
| 沙盒执行保证 Skill 修改的安全性 | Ch09 质量检查 |
| 知识修复饱和的发现——说明 Skill 改进不是线性的 | Ch10 何时停止迭代 |

---

### 2.9 学术综述论文：Agent Skills 的理论框架

| 论文 | 内容 |
|------|------|
| arxiv.org/abs/2602.12430（2025-02） | Agent Skills for LLMs: Architecture, Acquisition, and Engineering |

#### 六种 Skill 获取方法论

| 方法 | 说明 | 自动化程度 |
|------|------|-----------|
| Manual Packaging | 人工将工作流打包为 SKILL.md | 最低 |
| Reinforcement Learning | 强化学习优化任务链 | 中 |
| Autonomous Discovery | 课程设计 + 环境建模自主掌握新接口 | 高 |
| Structured Engineering | 将专家知识映射为参数化执行图 | 中 |
| Dynamic Composition | 动态组合推理模块解决复杂任务 | 高 |
| Multi-Agent Compression | 将多 Agent 协调压缩为单 Agent Skill 库 | 高 |

#### 核心洞察

> "Skills **prepare the agent to solve a problem** by encoding procedural strategies rather than executing atomic functions."

Skill 不是工具——工具执行原子操作，Skill 编码**解决问题的策略**。

> "The field is transitioning from temporary prompts to auditable, modular packages that preserve institutional knowledge."

Skill 工程的本质是将临时性 Prompt 转化为**可审计的、模块化的知识包**。

---

## 三、横向对比总结

### 3.1 核心维度对比

| 维度 | Anthropic Skill-Creator | LangGPT | DSPy | Promptfoo | EvoSkill/EvoSkills | SkillForge |
|------|------------------------|---------|------|-----------|-------------------|------------|
| **创建方式** | 人机协作 | 人工模板 | 程序化声明 | N/A（专注评估） | 全自动进化 | 全自动进化 |
| **测试机制** | 内建 eval 系统 | 无 | metric 函数 | 完整断言体系 | 自动 held-out | 自动诊断 |
| **优化方法** | 人工反馈 + description 自动化 | 无 | 贝叶斯优化 | 对比矩阵 | GEPA/DSPy | 四维诊断 |
| **输出格式** | SKILL.md | 结构化 Prompt | DSPy Module | 评估报告 | SKILL.md 兼容 | Skill 包 |
| **门槛** | 低（自然语言交互） | 低（模板填写） | 高（需编程） | 中（YAML 配置） | 高（需配置框架） | 高（需企业数据） |
| **迭代闭环** | 完整 | 无 | 自动化 | 手动分析 | 全自动 | 全自动 |
| **人类角色** | 决策者 + 审查者 | 作者 | 度量函数设计者 | 分析者 | 旁观者 | 旁观者 |

### 3.2 最佳实践提取

从所有方案中提炼出 **Anthropic Skill-Creator 没有但其他方案有的更优实践**：

#### 实践 1: 确定性断言体系（来自 Promptfoo）

Anthropic skill-creator 的断言是自由文本（"The output includes X"），由 LLM grader 评估。Promptfoo 提供了**确定性断言**（`contains`, `is-json`, `rouge-n`）和**轨迹断言**（`trajectory:tool-sequence`）——这些可以在不依赖 LLM 的情况下自动验证，**更快、更便宜、更可靠**。

**建议**：在 Skill 测试中混合使用确定性断言（结构/格式检查）和 LLM 断言（语义/质量检查）。

#### 实践 2: 生成器-验证器隔离（来自 EvoSkills）

Anthropic skill-creator 让创建 Skill 的同一个 Agent 也参与评估。EvoSkills 证明了**信息隔离**可以打破确认偏误，显著提升进化效果（32% → 75%）。

**建议**：在手工迭代 Skill 时，让一个"新鲜的"Agent（没有看过 Skill 源码的）来测试效果——模拟真实用户体验。

#### 实践 3: 四维诊断框架（来自 SkillForge）

Anthropic skill-creator 的改进建议是综合性的。SkillForge 将诊断分为四个独立维度——**知识、工具使用、澄清策略、语气**——然后并行分析。这使得改进方向更精确。

**建议**：当 Skill 表现不佳时，从这四个维度分别诊断，而非笼统地"改进"。

#### 实践 4: 知识饱和曲线（来自 SkillForge）

SkillForge 发现知识类修复很快饱和（收益递减），但工具和风格类修复可以持续改进。这意味着：

**建议**：如果多轮迭代后 Skill 的知识维度不再改进，转而关注工具编排和输出风格。

#### 实践 5: 合成测试数据（来自 Skill-Optimizer, EvoSkills）

Anthropic skill-creator 需要用户手工设计测试用例。DSPy 和 EvoSkills 都支持**自动生成合成测试数据**，降低测试成本。

**建议**：可以让 LLM 生成初始测试用例，人工审核后使用——兼顾质量和效率。

#### 实践 6: 质量门禁自动化（来自 Skill-Tester）

Anthropic skill-creator 关注的是单个 Skill 的开发循环。Skill-Tester 关注的是**仓库级别**的质量门禁——每次提交都自动验证。

**建议**：对于团队共享的 Skill 仓库，应该建立 CI/CD 级别的质量检查。

#### 实践 7: 失败驱动发现（来自 EvoSkill）

Anthropic skill-creator 从用户意图出发设计 Skill。EvoSkill 从 Agent 的**失败轨迹**出发发现 Skill——这是一种完全不同的创建路径。

**建议**：在日常使用 Agent 时，记录 Agent 做得不好的场景——这些就是潜在 Skill 的种子。

---

## 四、对 Skill-Book 各章的具体建议

| 章节 | 可新增/强化的内容 | 来源方案 |
|------|------------------|---------|
| Ch01 你好 Skill | Skill vs Prompt vs Tool 的定位辨析：Skill 编码"解决问题的策略" | 学术综述 |
| Ch02 Description | Promptfoo 的 `skill-used` 断言验证触发准确性 | Promptfoo |
| Ch03 可执行指令 | LangGPT 的 Role-Skills-Constraints 三元组作为对比 | LangGPT |
| Ch06 模板与示例 | DSPy 的"指令+示例联合优化"思想 | DSPy |
| Ch09 质量检查 | EvoSkills 的"生成器-验证器隔离"防确认偏误 | EvoSkills |
| Ch10 测试与调优 | Promptfoo 断言体系（确定性+轨迹+模型辅助三层）；SkillForge 四维诊断 | Promptfoo, SkillForge |
| Ch10 迭代循环 | 知识修复饱和曲线——何时停止迭代的科学依据 | SkillForge |
| Ch12 元技能 | EvoSkill 的"失败驱动发现"作为人工设计的互补路径 | EvoSkill |
| 附录 | 本调研报告可作为附录参考 | 全部 |

---

## 五、参考资源

| 资源 | 链接 |
|------|------|
| LangGPT 仓库 | https://github.com/langgptai/LangGPT |
| LangGPT 论文 | https://arxiv.org/abs/2402.16929 |
| DSPy 官网 | https://dspy.ai/ |
| DSPy 优化器文档 | https://dspy.ai/learn/optimization/optimizers/ |
| Skill-Optimizer 仓库 | https://github.com/Ash-Blanc/skill-optimizer |
| Promptfoo 仓库 | https://github.com/promptfoo/promptfoo |
| Promptfoo 断言文档 | https://www.promptfoo.dev/docs/configuration/expected-outputs/ |
| Skill-Tester | https://github.com/alirezarezvani/claude-skills |
| EvoSkill 仓库 | https://github.com/sentient-agi/EvoSkill |
| EvoSkill 论文 | https://arxiv.org/abs/2603.02766 |
| EvoSkills 官网 | https://evoskills.net/ |
| EvoSkills 论文 | https://arxiv.org/html/2604.01687v1 |
| SkillForge 论文 | https://arxiv.org/html/2604.08618v1 |
| Agent Skills 综述 | https://arxiv.org/abs/2602.12430 |
| Skill Engineering 文章 | https://pub.towardsai.net/skill-engineering-in-2026 |
