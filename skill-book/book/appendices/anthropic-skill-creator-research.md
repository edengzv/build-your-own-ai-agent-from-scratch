# Anthropic Skill-Creator 调研报告：原理、架构与方法论

> 调研时间：2026-04-19
> 数据来源：github.com/anthropics/skills, agentskills.io/specification, Anthropic 工程博客
> 关联章节：Ch05（知识加载）、Ch10（测试与调优）、Ch12（元技能）

---

## 一、定位与概览

### 1.1 什么是 Skill-Creator

Skill-creator 是 Anthropic 官方 `anthropics/skills` 仓库中的**元技能（meta-skill）**——一个用来创建、测试、迭代优化其他 Skill 的 Skill。它体现了"Skills all the way down"的设计哲学：用 Skill 的方法论来构建 Skill 本身。

### 1.2 仓库结构

```
anthropics/skills/
├── .claude-plugin/     # Claude Code 插件配置
├── skills/             # 所有 Skill 目录
│   ├── skill-creator/  # 元技能
│   │   ├── SKILL.md    # 核心指令（485 行）
│   │   ├── agents/     # 子 Agent 指令（grader, comparator, analyzer）
│   │   ├── assets/     # HTML 模板（eval_review.html）
│   │   ├── eval-viewer/# 评估结果可视化查看器
│   │   ├── references/ # schemas.md（JSON 数据结构定义）
│   │   ├── scripts/    # 自动化脚本（aggregate_benchmark, run_loop 等）
│   │   └── LICENSE.txt
│   ├── docx/           # Word 文档 Skill（生产级）
│   ├── pdf/            # PDF 处理 Skill（生产级）
│   ├── pptx/           # PowerPoint Skill（生产级）
│   └── xlsx/           # Excel Skill（生产级）
├── spec/               # Agent Skills 规范（→ agentskills.io）
├── template/           # Skill 模板
└── README.md
```

### 1.3 开放标准

Anthropic 已将 Skill 格式推动为行业开放标准，规范发布在 agentskills.io/specification。这意味着 Skill 不绑定 Claude——任何 Agent 系统都可以实现这套规范。

---

## 二、Agent Skills 规范（Specification）

### 2.1 SKILL.md 格式

每个 Skill 的核心是一个 `SKILL.md` 文件，包含 YAML Frontmatter + Markdown 正文。

#### 必填字段

| 字段 | 约束 | 说明 |
|------|------|------|
| `name` | 最长 64 字符，仅小写字母+数字+连字符，不能以连字符开头/结尾，不能有连续连字符，必须匹配目录名 | Skill 唯一标识符 |
| `description` | 最长 1024 字符，非空 | 描述做什么 + 何时触发，是 Agent 决定是否加载的唯一依据 |

#### 可选字段

| 字段 | 约束 | 说明 |
|------|------|------|
| `license` | 无限制 | 许可证名称或文件引用 |
| `compatibility` | 最长 500 字符 | 环境要求（产品、系统包、网络等） |
| `metadata` | key-value 映射 | 自定义元数据（author, version 等） |
| `allowed-tools` | 空格分隔的工具列表 | 预授权工具（实验性） |

#### 最小示例

```markdown
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

#### 完整示例

```markdown
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---
```

### 2.2 目录结构规范

```
skill-name/
├── SKILL.md          # 必须：元数据 + 指令
├── scripts/          # 可选：可执行代码（确定性/重复任务）
├── references/       # 可选：参考文档（按需加载）
├── assets/           # 可选：模板、图片、字体等静态资源
└── ...               # 任意附加文件
```

### 2.3 三层渐进式加载（Progressive Disclosure）

这是 Skill 系统的**核心设计原则**：

```
Layer 1: Metadata（~100 tokens）
  ├── 始终在上下文中
  └── Agent 只看到 name + description
  
Layer 2: SKILL.md body（< 5000 tokens，推荐 < 500 行）
  ├── 技能激活时加载
  └── 包含核心指令、步骤、示例
  
Layer 3: Bundled resources（无限制）
  ├── 按需加载
  ├── scripts/ → 可直接执行，不需要加载进上下文
  ├── references/ → Agent 需要时读取
  └── assets/ → 模板、静态资源
```

**关键洞察**：Layer 3 中的脚本可以**不加载进上下文就直接执行**。这意味着复杂的确定性逻辑（数据处理、格式转换、统计聚合）应该写成脚本放在 `scripts/` 中，而不是在 SKILL.md 里用自然语言描述算法。

#### 文件引用规范

- 使用从 Skill 根目录的相对路径
- 引用深度保持一层（所有 references 从 SKILL.md 直接链接）
- 超过 100 行的 reference 文件应在顶部附目录
- 避免多层嵌套引用链

---

## 三、Skill-Creator 工作流详解

### 3.1 完整流程

Skill-creator 定义了一个闭环的**创建-测试-迭代**循环：

```
Phase 1: 需求理解
  ├── ① 捕获意图（Capture Intent）
  │     ├── 从对话历史提取线索
  │     └── 确认4个核心问题：做什么 / 何时触发 / 输出格式 / 是否需要测试
  └── ② 访谈与研究（Interview and Research）
        ├── 主动追问：边界情况、输入输出格式、成功标准
        └── 利用 MCP 搜索相关文档和已有 Skill

Phase 2: 编写
  └── ③ 编写 SKILL.md 草稿
        ├── 填充所有组件
        └── 遵循 Skill Writing Guide

Phase 3: 验证循环
  ├── ④ 创建测试用例（2-3 个真实场景）
  ├── ⑤ 并行运行测试
  │     ├── with-skill 运行（使用 Skill 执行任务）
  │     └── baseline 运行（无 Skill 或旧版 Skill）
  ├── ⑥ 编写断言 + 定量评估
  ├── ⑦ 打分 → 聚合 → 启动可视化查看器
  └── ⑧ 用户反馈 → 改进 → 重复 ④-⑧

Phase 4: 优化
  ├── ⑨ 描述优化（Description Optimization）
  │     └── 自动化评估循环
  └── ⑩ 打包发布
```

### 3.2 测试用例设计

Skill-creator 要求测试用例必须是**真实用户会说的话**，而非抽象请求：

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": ["evals/files/sample1.pdf"],
      "expectations": [
        "The output includes X",
        "The skill used script Y"
      ]
    }
  ]
}
```

### 3.3 A/B 对比测试

每个测试用例同时运行两个版本，在同一轮次并行发起：

- **创建新 Skill 时**：with_skill vs without_skill（无 Skill）
- **改进现有 Skill 时**：with_skill vs old_skill（旧版快照）

### 3.4 评估体系

#### 定量评估（Quantitative）

```json
// grading.json — 断言评分结果
{
  "expectations": [
    {
      "text": "The output includes the name 'John Smith'",
      "passed": true,
      "evidence": "Found in transcript Step 3"
    }
  ],
  "summary": {
    "passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67
  },
  "execution_metrics": {
    "tool_calls": {"Read": 5, "Write": 2, "Bash": 8},
    "total_tool_calls": 15
  }
}
```

```json
// benchmark.json — 跨版本对比
// 包含 pass_rate, time, tokens 的 mean ± stddev 和 delta
```

#### 定性评估（Qualitative）

通过 `eval-viewer/generate_review.py` 生成 HTML 查看器，包含：

- **Outputs 标签页**：逐个查看测试用例的输出，支持反馈输入
- **Benchmark 标签页**：定量统计对比（pass rate、时间、token 用量）
- **Previous Output**（迭代 2+）：折叠显示上一轮输出
- **Previous Feedback**（迭代 2+）：显示上一轮的评论

用户反馈保存为 `feedback.json`：

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "chart is missing axis labels"},
    {"run_id": "eval-1-with_skill", "feedback": ""},
    {"run_id": "eval-2-with_skill", "feedback": "perfect, love this"}
  ],
  "status": "complete"
}
```

空反馈意味着用户认为该项没问题。

### 3.5 描述优化循环（Description Optimization）

这是 Skill-creator 最精巧的部分之一——自动化优化 description 的触发准确性：

**Step 1: 生成触发评估查询**

创建 20 个评估查询（8-10 个 should-trigger + 8-10 个 should-not-trigger）：

```json
[
  {"query": "ok so my boss just sent me this xlsx file...", "should_trigger": true},
  {"query": "write me a fibonacci function", "should_trigger": false}
]
```

关键要求：
- 查询必须**真实且具体**（包含文件路径、个人背景、具体细节）
- should-not-trigger 查询必须是**近似误匹配**，而非明显无关的请求
- 避免过于简单的测试——简单查询不会触发任何 Skill，无法测试 description 质量

**Step 2: 自动化优化**

```bash
python -m scripts.run_loop \
  --eval-set <eval.json> \
  --skill-path <skill> \
  --model <model-id> \
  --max-iterations 5
```

优化过程：
1. 将 20 个查询按 **60/40** 分为训练集和测试集
2. 每个查询运行 **3 次**以获得可靠触发率
3. 分析失败案例，提出 description 改进建议
4. 在训练集和测试集上重新评估
5. 最多迭代 5 次
6. **按测试集分数选择最佳 description**（避免过拟合）

**触发机制原理**：

Agent 在 `available_skills` 列表中看到所有 Skill 的 name + description。关键洞察：Agent **只会在它无法独立完成任务时才会咨询 Skill**。简单的一步操作（如"读这个 PDF"）即使 description 完美匹配也可能不触发——因为 Agent 认为自己能直接处理。复杂的、多步骤的、专业化的查询才会可靠地触发 Skill。

### 3.6 子 Agent 体系

Skill-creator 使用了多个专门化子 Agent：

| 子 Agent | 文件 | 职责 |
|---------|------|------|
| Executor | （内联指令） | 执行测试用例（with-skill / baseline） |
| Grader | `agents/grader.md` | 评估断言是否通过 |
| Comparator | `agents/comparator.md` | 盲比较两个版本的输出质量 |
| Analyzer | `agents/analyzer.md` | 分析基准数据，发现隐藏模式 |

---

## 四、Skill 编写核心理念

### 4.1 解释 Why，而非堆砌 MUST

> "Try hard to explain the **why** behind everything you're asking the model to do. Today's LLMs are *smart*. They have good theory of mind and when given a good harness can go beyond rote instructions. If you find yourself writing ALWAYS or NEVER in all caps, that's a yellow flag — reframe and explain the reasoning so that the model understands why the thing you're asking for is important."

这是 Anthropic 从大规模实践中提炼的核心洞察：**不要把 Skill 写成法条，而是写成教程**。

- **坏的写法**: `ALWAYS use semicolons. NEVER use tabs.`
- **好的写法**: `We use semicolons because our linter requires them, and the CI pipeline will reject PRs without them. Use spaces instead of tabs because our formatter (prettier) is configured for 2-space indentation.`

### 4.2 Description 要"稍微 pushy"

Anthropic 发现模型倾向于**"欠触发"（under-trigger）**——在应该使用 Skill 的时候不去使用它。因此建议 description 写得覆盖面更广：

- **差**: `"How to build a simple fast dashboard to display internal Anthropic data."`
- **好**: `"How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"`

### 4.3 从反馈中泛化，而非过拟合

> "We're trying to create skills that can be used a million times across many different prompts. Rather than put in fiddly overfitty changes, or oppressively constrictive MUSTs, if there's some stubborn issue, you might try branching out and using different metaphors."

迭代改进时，核心原则是**泛化而非特化**——不要为了让某个测试用例通过而添加狭窄的规则。

### 4.4 发现重复模式 → 提取脚本

> "Read the transcripts from the test runs. If all 3 test cases resulted in the subagent writing a similar helper script, that's a strong signal the skill should **bundle that script**."

当多个测试运行都独立写出了类似的辅助代码时，说明这个逻辑应该被提取到 `scripts/` 目录中，让每次调用复用而非重新发明。

### 4.5 保持精简

> "Remove things that aren't pulling their weight. Make sure to read the transcripts, not just the final outputs — if it looks like the skill is making the model waste a bunch of time doing things that are unproductive, you can try getting rid of the parts of the skill that are making it do that."

通过阅读测试运行的完整 transcript（不仅是最终输出），识别 Skill 中导致模型浪费时间的指令，果断删除。

### 4.6 面向不同用户群体的沟通

> "There's a trend now where the power of Claude is inspiring plumbers to open up their terminals, parents and grandparents to google 'how to install npm'."

Skill-creator 特别注意用户可能不懂技术术语，要求根据上下文线索调整沟通方式。术语使用指南：

- "evaluation"、"benchmark"：边界可接受
- "JSON"、"assertion"：需要看到用户的技术水平线索后再使用

### 4.7 无恶意原则（Principle of Lack of Surprise）

> "Skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described."

Skill 的行为不应该让用户在知道 description 后仍然感到惊讶。

---

## 五、与我们的 Skill 系统的关系

### 5.1 对 Hermas 书（ch05 知识加载）的映射

| 维度 | Hermas ch05 | Anthropic Skill System |
|------|-------------|------------------------|
| 加载层次 | 2 层（目录摘要 + 内容加载） | 3 层（metadata + body + resources） |
| 触发机制 | Agent 自主判断 + `load_skill` 工具 | Agent 自主判断（内置于平台） |
| 资源管理 | 单文件 SKILL.md | 多文件目录（scripts/、references/、assets/） |
| 测试框架 | 无 | 完整的 eval 系统 + 可视化 |
| 描述优化 | 设计原则指导 | 自动化优化循环（训练/测试集） |
| 编写哲学 | 规则化指令 | 解释 Why + 泛化优先 |

### 5.2 对 Skill-Book 各章的启示

| Skill-Book 章节 | 可借鉴的 Anthropic 实践 |
|-----------------|------------------------|
| Ch02 Description | under-triggering 问题、description 要 "pushy"、触发评估方法 |
| Ch03 可执行指令 | "解释 Why 而非堆砌 MUST" 的写作哲学 |
| Ch07 渐进式加载 | Layer 3 "脚本不加载就能执行" 的洞察 |
| Ch09 质量检查 | grading.json 的断言评分体系 |
| Ch10 测试调优 | A/B 对比、description optimization loop、60/40 训练/测试集 |
| Ch11 案例解剖 | skill-creator 本身是最好的解剖案例 |
| Ch12 元技能 | skill-creator 的完整工作流是本章的核心参考 |

---

## 六、Skill-Creator SKILL.md 结构速查

### 6.1 Frontmatter

```yaml
---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill 
  performance. Use when users want to create a skill from scratch, edit, or optimize an 
  existing skill, run evals to test a skill, benchmark skill performance with variance 
  analysis, or optimize a skill's description for better triggering accuracy.
---
```

### 6.2 主体结构（485 行）

```
# Skill Creator
├── 高层概述（创建-测试-迭代循环）
├── 沟通风格指南（面向不同技术水平用户）
│
├── ## Creating a skill
│   ├── Capture Intent（4 个核心问题）
│   ├── Interview and Research（主动追问 + MCP 研究）
│   ├── Write the SKILL.md
│   │   ├── Skill Writing Guide
│   │   │   ├── Anatomy of a Skill（目录结构）
│   │   │   ├── Progressive Disclosure（三层加载）
│   │   │   ├── Principle of Lack of Surprise（安全原则）
│   │   │   └── Writing Patterns（输出格式、示例模式）
│   │   └── Writing Style（解释 Why、泛化思维）
│   └── Test Cases（evals.json 格式）
│
├── ## Running and evaluating test cases
│   ├── Step 1: 并行运行（with-skill + baseline）
│   ├── Step 2: 编写断言（利用等待时间）
│   ├── Step 3: 捕获 timing 数据
│   ├── Step 4: 打分 → 聚合 → 分析 → 启动查看器
│   └── Step 5: 读取用户反馈
│
├── ## Improving the skill
│   ├── 改进思维：泛化、精简、解释 Why、提取脚本
│   └── 迭代循环
│
├── ## Advanced: Blind comparison（盲比较）
│
├── ## Description Optimization
│   ├── Step 1: 生成触发评估查询（20 个）
│   ├── Step 2: 用户审核
│   ├── Step 3: 自动化优化循环（60/40 分割、3 次运行、5 轮迭代）
│   ├── 触发机制原理说明
│   └── Step 4: 应用最佳 description
│
├── ## Package and Present
│
├── ## Claude.ai-specific instructions（无子 Agent 时的适配）
│
└── ## Reference files（子 Agent 文档索引）
```

---

## 七、关键 JSON Schema 速查

### evals.json（测试用例定义）

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's example prompt",
      "expected_output": "Description of expected result",
      "files": ["evals/files/sample1.pdf"],
      "expectations": ["The output includes X"]
    }
  ]
}
```

### grading.json（断言评分结果）

```json
{
  "expectations": [
    {"text": "assertion text", "passed": true, "evidence": "proof"}
  ],
  "summary": {"passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67},
  "execution_metrics": {"tool_calls": {"Read": 5, "Write": 2}},
  "timing": {"total_duration_seconds": 191.0}
}
```

### history.json（版本进化追踪）

```json
{
  "skill_name": "pdf",
  "current_best": "v2",
  "iterations": [
    {"version": "v0", "expectation_pass_rate": 0.65, "grading_result": "baseline"},
    {"version": "v1", "expectation_pass_rate": 0.75, "grading_result": "won"},
    {"version": "v2", "expectation_pass_rate": 0.85, "grading_result": "won", "is_current_best": true}
  ]
}
```

---

## 八、参考资源

| 资源 | 链接 |
|------|------|
| Anthropic Skills 仓库 | https://github.com/anthropics/skills |
| Agent Skills 规范 | https://agentskills.io/specification |
| 工程博客：Equipping Agents with Skills | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills |
| Complete Guide to Building Skills (PDF) | https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf |
| DeepLearning.AI 短课程 | https://www.deeplearning.ai/short-courses/agent-skills-with-anthropic/ |
| Skills 深度解析（腾讯云） | https://cloud.tencent.com/developer/article/2630018 |
| Deep Dive SKILL.md | https://abvijaykumar.medium.com/deep-dive-skill-md-part-1-2-09fc9a536996 |
