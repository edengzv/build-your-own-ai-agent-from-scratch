# Skill Book 升级计划 v2

> 基于 5 份 appendices 调研材料（~103KB）与现有 12 章正文的 Gap Analysis
> 制定时间：2026-04-19

---

## 一、Gap Analysis 总览

### 调研材料矩阵

| 调研文件 | 核心内容 | 已吸收 | 未吸收 |
|---------|---------|--------|--------|
| anthropic-skill-creator-research.md | Anthropic 官方 skill-creator 架构、agentskills.io 规范、评估体系、description 优化循环 | 三层加载架构(Ch7)、Meta-skill 概念(Ch12) | **Explain Why 哲学、description optimization loop、子 Agent 体系、eval 系统、触发机制原理** |
| skill-creator-ecosystem-research.md | 8 个竞品/学术方案（LangGPT、DSPy、Promptfoo、EvoSkill/EvoSkills、SkillForge） | 无 | **几乎全部未吸收——断言分类体系、程序化优化、生成器-验证器隔离、四维诊断、知识饱和曲线、失败驱动发现** |
| openclaw-skills-research.md | OpenClaw 5,400+ Skill 生态、TOP 20 优秀 Skill 分析、最佳实践体系 | 无 | **新工作流模式（5种）、极简设计典范、安全模型设计、状态持久化、Anti-Patterns 清单** |
| openclaw-skill-best-practices.md | 13 大类最佳实践、自由度匹配、护栏设计、多模型兼容、进阶实践 | 部分(Ch3脆弱度) | **指令语言规范、Guardrails 设计模式、双循环架构、完全自主模式、工作区标准化、跨 Skill 编排** |
| global-agent-skills-ecosystem.md | 全球生态版图、9 大平台兼容、2026 趋势、官方 Skill 合集 | 部分(Ch12展望) | **完整生态版图、跨平台标准化、领域纵深策略、自主执行趋势、Vercel/Orchestra 架构** |

### 吸收率评估

- **已充分吸收**: ~25%（三层架构、基础 Meta-skill、lovstudio 案例）
- **部分吸收**: ~15%（脆弱度概念、生态展望）
- **完全未吸收**: ~60%（评估体系、竞品对比、高级设计模式、全球生态、学术前沿）

---

## 二、升级优先级排序

按 **"对读者价值 × 材料成熟度 × 改动规模"** 三维评估：

### P0 — 必须升级（核心方法论缺失）

| # | 升级项 | 影响章节 | 来源 | 理由 |
|---|--------|---------|------|------|
| 1 | **"Explain Why, Not MUST" 写作哲学** | Ch03 | anthropic-research | Anthropic 核心洞察，直接颠覆当前 Ch3 的"五要素"框架——当前偏向规则化，应加入"解释 Why"维度 |
| 2 | **Description Optimization Loop** | Ch10 | anthropic-research | 当前 Ch10 只有手动 A/B 测试，缺少 Anthropic 的自动化 description 优化循环（20 查询、60/40 分割、5 轮迭代） |
| 3 | **5 种工作流设计模式** | Ch04 | openclaw-best-practices | 当前 Ch4 只教 Multi-Pass 一种模式，但实际存在 5 种主要模式（清单式、诊断-修复-验证、循环反馈、条件分支、量化决策） |
| 4 | **Promptfoo 断言分类体系** | Ch10 | ecosystem-research | 当前 Ch10 缺少系统的断言框架，Promptfoo 的三层断言（确定性 + 轨迹 + 模型辅助）填补了这个关键空白 |
| 5 | **Guardrails & Anti-Patterns 设计模式** | Ch09 或新增一节 | openclaw-research | 当前 Ch9 只讲 Quality Checklist，缺少"告诉 Agent 什么不该做"这个同等重要的设计维度 |

### P1 — 强烈建议（显著提升深度）

| # | 升级项 | 影响章节 | 来源 | 理由 |
|---|--------|---------|------|------|
| 6 | **指令语言规范** | Ch03 | openclaw-best-practices | 祈使句 > 陈述句、表格 > 段落、避免第二人称——具体可操作的写作规范 |
| 7 | **自由度匹配矩阵** | Ch03 | openclaw-best-practices | 将 Ch3 的"脆弱度频谱"概念系统化为窄桥/开阔地模型 |
| 8 | **Description "pushy" 策略** | Ch02 | anthropic-research | Anthropic 发现模型倾向"欠触发"，description 应更积极——当前 Ch2 未提及这个洞察 |
| 9 | **Anthropic Skill-Creator 完整架构** | Ch12 | anthropic-research | 当前 Ch12 的 skill-creator 是简化版，应对比 Anthropic 官方 485 行版本的子 Agent 体系和 eval 系统 |
| 10 | **知识饱和曲线 & 何时停止迭代** | Ch10 | ecosystem-research (SkillForge) | "知识修复很快饱和，工具和风格修复可持续改进"——迭代策略的科学依据 |
| 11 | **Scripts-First 原则强化** | Ch07 | global-ecosystem (Vercel) | "脚本执行不消耗上下文（只有输出消耗）"——当前 Ch7 提到了脚本但未强调这个关键 token 经济学 |
| 12 | **生成器-验证器隔离** | Ch09 | ecosystem-research (EvoSkills) | 自检的确认偏误问题——让新鲜 Agent 测试 Skill 效果，而非创作者自己测 |

### P2 — 建议升级（扩展视野）

| # | 升级项 | 影响章节 | 来源 | 理由 |
|---|--------|---------|------|------|
| 13 | **全球 Skill 生态版图** | Ch12 或附录 | global-ecosystem | 读者需要知道 Vercel 25K、Orchestra 7K、OpenSkills 9K 等生态的存在和定位 |
| 14 | **跨平台兼容性** | Ch01 或 Ch12 | global-ecosystem | SKILL.md 已被 9 个平台采纳——这个事实大幅提升读者学习 Skill 的动力 |
| 15 | **OpenClaw TOP 10 案例** | Ch11 | openclaw-research | deslop（30 行极简）、checkmate（Worker/Judge）、emergency-rescue（统一诊断模式）等优秀案例 |
| 16 | **双循环架构 & 完全自主模式** | Ch04 或 Ch08 | global-ecosystem (Orchestra) | 面向复杂长期任务的高级架构模式 |
| 17 | **EvoSkill/EvoSkills 自动 Skill 发现** | Ch12 | ecosystem-research | 从失败轨迹自动提炼 Skill——人工设计的互补路径 |
| 18 | **状态持久化设计** | Ch04 或 Ch08 | openclaw-best-practices | 可中断/恢复的 Skill 需要状态文件设计——当前未涉及 |
| 19 | **设计反模式清单** | 附录或 Ch09 | openclaw-research | 10 个常见反模式（信息轰炸、重复造轮子、模糊触发、无护栏…） |
| 20 | **Skill 发布检查清单** | Ch12 或附录 | openclaw-best-practices | 发布前 20+ 项检查——比 Ch9 的单 Skill Checklist 更全面 |

### P3 — 可选升级（学术前沿 / 长远价值）

| # | 升级项 | 影响章节 | 来源 | 理由 |
|---|--------|---------|------|------|
| 21 | **DSPy 程序化优化** | Ch10 附录 | ecosystem-research | "声明意图，让优化器自动找最佳 Prompt"——前沿方向但门槛较高 |
| 22 | **SkillForge 四维诊断** | Ch10 | ecosystem-research | 知识/工具/澄清/语气四维并行诊断——精细的改进方法论 |
| 23 | **LangGPT 结构化模板对比** | Ch03 | ecosystem-research | Role-Skills-Constraints 三元组与 SKILL.md 五要素的对比分析 |
| 24 | **agentskills.io 官方规范** | Ch01 或附录 | anthropic-research | Anthropic 推动的开放标准，name 字段的精确约束（64 字符、kebab-case 等） |
| 25 | **合成测试数据生成** | Ch10 | ecosystem-research | 用 LLM 生成测试用例再人工审核——降低测试成本的实用技巧 |

---

## 三、具体升级方案

### 方案 A: 章节内升级（修改现有章节）

#### Ch02 Description — 新增 2 节

```
+ 2.X "Description 的隐形陷阱：欠触发问题"
  - Anthropic 洞察：模型倾向 under-trigger
  - "pushy" 策略：覆盖面 > 精确度
  - 触发机制原理：Agent 只在无法独立完成时才查阅 Skill
  
+ 2.Y "自动化 Description 优化"（预告 Ch10 深入）
  - 20 个评估查询（10 should-trigger + 10 should-not-trigger）
  - 60/40 训练/测试集分割
  - 近似误匹配 > 明显无关（测试要有难度）
```

#### Ch03 可执行指令 — 新增 2 节 + 修订 1 节

```
+ 3.X "解释 Why，而非堆砌 MUST"
  - Anthropic 核心哲学引用
  - 坏: "ALWAYS use semicolons"
  - 好: "We use semicolons because our linter requires them..."
  - "今天的 LLM 很聪明——给它理由，它比盲从指令做得更好"

+ 3.Y "指令语言的匠人规范"
  - 祈使句 > 陈述句
  - 表格 > 列表 > 段落
  - 代码示例 > 文字描述
  - 正反对照 > 单一示例
  - 避免第二人称

修订 3.3 脆弱度频谱 → 重构为"自由度匹配矩阵"
  - 窄桥型（数据库迁移、安全操作）→ 低自由度 → 精确命令
  - 开阔地（代码审查、设计）→ 高自由度 → 方向性指引
  - 工具依赖型 → 中自由度 → 条件分支
```

#### Ch04 多步工作流 — 扩展为"工作流设计模式"

```
当前: 只讲 Multi-Pass 一种模式
升级: 增加 4 种模式，将 Ch4 重新定位为"工作流设计模式库"

+ 4.X Pattern 2: 诊断-修复-验证 (Diagnose-Fix-Verify)
  - 案例: emergency-rescue（20+ 场景统一此模式）
  - 适用: 排障、修复、恢复类任务

+ 4.Y Pattern 3: 循环反馈 (Iterative Feedback Loop)
  - 案例: checkmate（Worker/Judge 架构）
  - 适用: 需要质量保证的迭代任务

+ 4.Z Pattern 4: 条件分支 (Decision Tree)
  - 案例: anti-pattern-czar（5 种模式的意图解析表）
  - 适用: 多模式/多意图的 Skill

+ 4.W Pattern 5: 量化决策 (Quantified Decision Matrix)
  - 案例: adaptive-reasoning（0-10 维度打分 + 阈值）
  - 适用: 需要自动选择行为级别的场景
```

#### Ch07 渐进式加载 — 强化 1 节

```
修订 7.3 scripts/ 目录设计
+ "脚本执行不消耗上下文"关键洞察（来自 Vercel）
  - 脚本代码不占上下文窗口
  - 只有脚本的输出（stdout）进入上下文
  - 因此：确定性操作应该尽可能封装为脚本
  - Vercel 规范: set -e + stderr/stdout 分离 + cleanup trap
```

#### Ch09 质量检查清单 — 新增 2 节

```
+ 9.X "Guardrails：告诉 Agent 什么不该做"
  - Guardrails 部分设计（必须包含"不可做"清单）
  - Anti-Patterns 部分设计（Agent 容易犯的错误清单）
  - 安全模型前置（高权限 Skill 必须声明）
  - 破坏性操作标记（⚠️）
  - 案例: deslop, checkmate, agent-self-reflection

+ 9.Y "打破确认偏误：生成器-验证器隔离"
  - EvoSkills 的核心洞察
  - 创作者自己测试的确认偏误问题
  - 实践建议：让"新鲜 Agent"测试你的 Skill
```

#### Ch10 测试与调优 — 大幅扩展（当前最薄弱的章节）

```
当前: 189 行，只有手动 A/B 测试和简单诊断
目标: 扩展到 350+ 行，系统化的评估方法论

+ 10.X "断言分类体系"（来自 Promptfoo）
  - 确定性断言: equals, contains, is-json, is-html
  - 轨迹断言: tool-used, tool-sequence, step-count
  - 模型辅助断言: llm-rubric, factuality, similarity
  - 混合使用: 确定性（格式检查）+ LLM（语义质量）

+ 10.Y "Description 自动化优化循环"
  - Anthropic 的 description optimization loop
  - Step 1: 生成 20 个评估查询
  - Step 2: 60/40 训练/测试集分割
  - Step 3: 每个查询运行 3 次
  - Step 4: 分析失败案例 → 改进 description
  - Step 5: 按测试集分数选最佳（防过拟合）
  - 最多 5 轮迭代

+ 10.Z "何时停止迭代：知识饱和曲线"
  - SkillForge 的发现: 知识修复很快饱和
  - 工具使用和输出风格修复可持续改进
  - 实践指导: 如果知识维度不再改进，转向工具编排和风格

修订 10.3 诊断问题根因 → 扩展为"四维诊断"
  - 维度 1: 知识（Skill 知道的是否足够？）
  - 维度 2: 工具使用（工具编排是否正确？）
  - 维度 3: 澄清策略（是否该问用户？）
  - 维度 4: 语气/风格（输出风格是否合适？）
```

#### Ch12 元技能 — 扩展 2 节

```
+ 12.X "Anthropic 官方 Skill-Creator 深度解析"
  - 485 行 SKILL.md 的完整架构速查
  - 子 Agent 体系: Executor / Grader / Comparator / Analyzer
  - eval-viewer 可视化系统
  - JSON Schema: evals.json, grading.json, history.json
  - 与本书简化版 skill-creator 的定位差异

+ 12.Y "自动化 Skill 发现：从失败中学习"
  - EvoSkill: 从失败轨迹自动提炼 Skill
  - EvoSkills: 生成器-验证器协同进化（32%→75%）
  - SkillForge: 从企业工单自动生成 Skill
  - 启示: 记录 Agent 做得不好的场景→这些是 Skill 的种子

修订 12.6 展望 → 融入全球生态版图
  - 9 大兼容平台列表
  - 主要 Skill 仓库（Vercel 25K, Orchestra 7K, OpenSkills 9K）
  - 2026 四大趋势: 自主执行、多 Agent 编排、Agentic IDE、领域纵深
```

### 方案 B: 新增内容

#### 新增附录 A: Skill 设计反模式清单

```
从 openclaw-research 提炼的 10 大反模式:
1. 信息轰炸（主文件几千行）
2. 重复造轮子（教模型已知知识）
3. 模糊触发（description 过于宽泛）
4. 无护栏（没有安全边界）
5. 代码内联过多
6. 缺乏验证步骤
7. 万能 Skill（试图做所有事情）
8. 硬编码（路径、API Key 写死）
9. 无示例（纯理论描述）
10. 忽略边界情况
```

#### 新增附录 B: Skill 发布前检查清单

```
从 openclaw-best-practices 提炼的 4 类 20+ 项检查:
- 核心质量（6 项）
- 结构完整性（4 项）
- 安全与可靠性（5 项）
- 代码与测试（8 项）
```

#### 新增附录 C: 全球 Skill 生态资源地图

```
从 global-ecosystem 整理:
- 8 大 Skill 集合仓库
- 5 大 Skill 发现平台
- 各平台官方文档链接
- 官方 Skill 合集索引（Anthropic 16个, OpenAI 18个, Google 4个, HuggingFace 4个）
```

---

## 四、升级工作量估算

| 优先级 | 升级项数 | 新增行数估算 | 章节影响 |
|--------|---------|------------|---------|
| P0 | 5 项 | ~500 行 | Ch02, Ch03, Ch04, Ch09, Ch10 |
| P1 | 7 项 | ~600 行 | Ch02, Ch03, Ch07, Ch09, Ch10, Ch12 |
| P2 | 8 项 | ~800 行 | Ch04, Ch08, Ch11, Ch12, 附录 |
| P3 | 5 项 | ~400 行 | Ch01, Ch03, Ch10, 附录 |
| **合计** | **25 项** | **~2,300 行** | **10/12 章 + 3 个附录** |

当前全书 5,025 行 → 升级后预计 ~7,300 行（+45%）

---

## 五、升级依赖关系

```
Ch03 (Explain Why + 指令规范 + 自由度矩阵)
  ↓ 被引用于
Ch04 (5 种工作流模式需要自由度概念)
  ↓ 被引用于
Ch09 (Guardrails 模式引用工作流中的"护栏"概念)
  ↓ 被引用于
Ch10 (断言体系和 description 优化引用质量检查)
  ↓ 被引用于
Ch12 (完整的 eval 系统引用测试方法论)
```

建议按此顺序执行升级: **Ch03 → Ch04 → Ch02 → Ch07 → Ch09 → Ch10 → Ch12 → Ch11 → 附录**

---

## 六、每章升级后的预期对比

| 章节 | 当前行数 | 当前评价 | 升级后行数 | 升级后提升点 |
|------|---------|---------|-----------|------------|
| Ch01 | 287 | 完整 | ~300 | +跨平台兼容性事实 |
| Ch02 | 330 | 良好 | ~400 | +pushy 策略, +触发机制原理 |
| Ch03 | 371 | 良好 | ~480 | +Explain Why 哲学, +指令规范, +自由度矩阵 |
| Ch04 | 248 | **偏薄** | ~420 | +4 种工作流模式（从 1→5） |
| Ch05 | 224 | 完整 | ~230 | 微调 |
| Ch06 | 235 | 完整 | ~240 | 微调 |
| Ch07 | 247 | 良好 | ~280 | +Scripts-First 关键洞察 |
| Ch08 | 217 | 完整 | ~250 | +状态持久化设计 |
| Ch09 | 241 | **缺失维度** | ~340 | +Guardrails/Anti-Patterns, +隔离验证 |
| Ch10 | 189 | **最薄弱** | ~380 | +断言体系, +description 优化, +四维诊断, +饱和曲线 |
| Ch11 | 486 | 良好(已更新) | ~550 | +OpenClaw 极简案例 |
| Ch12 | 436 | 良好(已更新) | ~550 | +Anthropic skill-creator, +自动发现, +全球生态 |

---

## 七、执行建议

### 推荐执行策略

**分 3 轮执行**:

- **第 1 轮 (P0)**：修复核心方法论缺失
  - Ch03 + Ch04 + Ch10（方法论三连击）
  - Ch02（description 补充）
  - Ch09（Guardrails 维度）

- **第 2 轮 (P1)**：深化技术深度
  - Ch07（Scripts-First）
  - Ch12（Anthropic skill-creator + 自动发现）
  - 各章细节修订

- **第 3 轮 (P2+P3)**：扩展视野
  - Ch11（更多案例）
  - 3 个新增附录
  - book-meta.md 更新
  - 全书一致性审查

### 质量保证

每轮升级后：
1. 检查章节间交叉引用的一致性
2. 确认新增内容与原有叙事的衔接
3. 更新 outline.md 和 roadmap.md
4. 更新 glossary.md 术语
5. 更新 bibliography.md 参考文献
