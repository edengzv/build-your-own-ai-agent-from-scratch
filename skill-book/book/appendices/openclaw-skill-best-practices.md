# OpenClaw SKILL.md 最佳实践手册 (Best Practices Handbook)

> 基于 TOP 20 优秀 Skills 源码分析和官方文档提炼
> 调研时间：2026-04-19

---

## 一、SKILL.md 文件结构规范

### 1.1 标准目录结构

```
my-skill/
├── SKILL.md              # 核心文件：YAML 元数据 + 指令正文（必须）
├── references/           # 按需加载的详细文档（可选）
│   ├── api-docs.md       # API 规范
│   ├── workflows.md      # 详细工作流
│   └── patterns.md       # 模式列表与代码模板
├── scripts/              # 可执行脚本（可选，不加载到上下文）
│   ├── run.py
│   └── analyzer.sh
└── assets/               # 模板、Schema、图片（可选，通过脚本访问）
    ├── template.json
    └── schema.xml
```

### 1.2 三层渐进式加载架构

```
Layer 1 - Metadata    总是加载    name + description（YAML frontmatter）
Layer 2 - Body        相关时加载  核心指令（SKILL.md 正文）
Layer 3 - Resources   按需加载    references/ scripts/ assets/
```

**核心原则**: Agent 只在 Skill 变得相关时读取 SKILL.md，并且只在需要时读取附加文件。

---

## 二、元数据设计 (Metadata Design)

### 2.1 YAML Frontmatter 规范

```yaml
---
name: my-skill-name          # 必须。kebab-case，仅小写字母+数字+连字符，最多64字符
description: >                # 必须。1-2句话，第三人称，最多1024字符
  Detect and fix TypeScript error handling anti-patterns with state
  persistence and approval workflows. Use when scanning a codebase
  for silent error failures, empty catches, or promise swallowing.
---
```

### 2.2 命名规范

| 规则 | 正确示例 | 错误示例 |
|------|---------|---------|
| 使用 kebab-case | `processing-pdfs` | `ProcessingPdfs`, `processing_pdfs` |
| 动名词结构优先 | `commit-formatting` | `commit-formatter-helper` |
| 避免模糊词 | `api-dev` | `api-utils`, `api-helper` |
| 禁用保留词 | `git-changelog` | `skill`, `tool`, `agent` |

### 2.3 Description 撰写要诀

**必须包含两个要素**: "做什么" + "何时用"

```yaml
# 优秀示例
description: >
  Format commit messages using the Conventional Commits specification.
  Use when creating commits, writing commit messages, or when the user
  mentions commits, git commits, or commit messages.

# 反面示例
description: A useful tool for managing your git workflow.  # 过于宽泛
description: I help you write better commits.                # 第一人称
```

**触发词嵌入技巧**: 在 description 中嵌入用户可能说的短语

```yaml
description: >
  Remove AI-style code slop from a branch. Use when asked to
  "remove AI slop", "clean up generated code style", or
  "review branch diff for weird comments".
```

---

## 三、正文写作规范 (Body Writing Standards)

### 3.1 篇幅控制

| 指标 | 建议值 | 硬性上限 |
|------|-------|---------|
| 主文件行数 | < 200 行 | 500 行 |
| 主文件词数 | < 2,000 词 | 5,000 词 |
| 单个 reference 文件 | < 5,000 词 | 10,000 词 |
| 超 100 行的 reference | 顶部必须附目录 | — |

### 3.2 指令语言

```markdown
# 使用祈使句
Load the configuration file.        (正确)
You should load the configuration.  (错误)

# 使用不定式结构
To validate the output, run the check script.  (正确)
If you need to validate, you should run...     (错误)

# 避免第二人称
Read the session history.           (正确)
You need to read the session.       (错误)
```

### 3.3 信息组织优先级

```
表格 > 列表 > 段落
代码示例 > 文字描述
正反对照 > 单一示例
```

**案例 — 用表格替代段落**:

```markdown
# 反面（段落描述）
When the user says "scan" or "detect" or "find", use SCAN mode.
When they say "review", "fix", or "help me fix", use REVIEW mode...

# 正面（表格呈现）
| User Says | Mode | Action |
|-----------|------|--------|
| "scan", "detect", "find" | SCAN | Run detector, save state |
| "review", "fix" | REVIEW | Interactive fix session |
| "auto", "fix all" | AUTO | Batch fix with guardrails |
```

### 3.4 引用深度控制

```markdown
# 正确: 单层引用（从主文件直接链接）
See [workflows.md](references/workflows.md) for detailed steps.
Read and apply: [slop-heuristics.md](references/slop-heuristics.md)

# 错误: 多层嵌套（references 文件又引用其他 references）
# references/workflows.md 中:
# See [sub-workflow.md](../references/sub-workflows/sub-workflow.md)  ← 避免
```

---

## 四、极简设计原则 (Minimalism Principles)

### 4.1 核心理念

> 上下文窗口是共享资源。Skill 应只补充模型未知的信息。

### 4.2 实践方法

**自检清单**:
- [ ] 每个句子是否提供了模型本身不知道的信息?
- [ ] 删掉这段话，Agent 的行为会变差吗?
- [ ] 这段内容能否移到 references/ 中按需加载?

**极简典范 — `deslop` Skill (约30行)**:

```markdown
---
name: deslop
description: Remove AI-style code slop from a branch...
allowed-tools: [Bash]
---

## When to use this skill
Use when asked to: "remove AI slop", "clean up generated code style"...

## Workflow
1. Set comparison base and inspect `git diff <base>...HEAD`.
2. Build candidate list using `rg` over added lines.
3. Review each candidate in full file context.
4. Remove only inconsistent slop; keep behavior and domain-valid guards.
5. Re-run project checks and fix regressions.
6. Report exact files changed.

## Slop checklist
Read and apply: [references/slop-heuristics.md](references/slop-heuristics.md)

## Guardrails
- Do not remove protections at trust boundaries.
- Do not replace real typing with weaker typing.
- Prefer minimal edits over broad rewrites.
```

**关键**: 30行主文件 + 1个 references 文件，实现了完整的功能描述和安全护栏。

---

## 五、工作流设计模式 (Workflow Design Patterns)

### Pattern 1: 清单式推进 (Checklist Progression)

适用于: 有确定步骤的线性任务

```markdown
## Workflow
Step 1: Gather recent sessions
Step 2: Read session history
Step 3: Analyze & extract insights
Step 4: Route insights to the right files
Step 5: Write the insights
Step 6: Summary
```

**案例**: `client-flow`（7步客户入职）, `agent-self-reflection`（6步自省流程）

### Pattern 2: 诊断-修复-验证 (Diagnose-Fix-Verify)

适用于: 问题排查和修复场景

```markdown
### Force-pushed to main

# DIAGNOSE: Check the reflog
git reflog show origin/main

# FIX: Restore the old state
git push origin <good-commit-hash>:main --force-with-lease

# VERIFY: Confirm the history
git log --oneline -10 origin/main
```

**案例**: `emergency-rescue`（20+场景统一此模式）

### Pattern 3: 循环反馈 (Iterative Feedback Loop)

适用于: 需要质量保证的任务

```
执行(Worker) → 评判(Judge) → 通过? → 输出
                             ↓ 不通过
                          反馈差距 → 重试
```

**案例**: `checkmate`（Worker/Judge 架构，最多10次迭代）

### Pattern 4: 条件分支 (Decision Tree)

适用于: 多模式/多意图的 Skill

```markdown
| User Says              | Mode   | Action                    |
|------------------------|--------|---------------------------|
| "scan", "detect"       | SCAN   | Run detector, save state  |
| "review", "fix"        | REVIEW | Interactive fix session    |
| "auto", "fix all"      | AUTO   | Batch fix with guardrails |
| "resume", "continue"   | RESUME | Load state, continue      |
| "report", "status"     | REPORT | Show current state        |
```

**案例**: `anti-pattern-czar`（5种模式的意图解析）

### Pattern 5: 量化决策 (Quantified Decision Matrix)

适用于: 需要根据条件自动选择行为

```markdown
| Signal              | Weight | Examples                    |
|---------------------|--------|-----------------------------|
| Multi-step logic    | +3     | Planning, proofs, debugging |
| Ambiguity           | +2     | Nuanced questions, trade-offs|
| Routine task        | -2     | Repetitive, clear answer    |

| Score | Action                              |
|-------|-------------------------------------|
| <= 2  | Stay fast. No reasoning needed.     |
| 3-5   | Standard response.                  |
| 6-7   | Enable reasoning silently.          |
| >= 8  | Activate extended thinking.         |
```

**案例**: `adaptive-reasoning`（0-10维度打分 + 阈值决策）

---

## 六、护栏与安全设计 (Guardrails & Safety)

### 6.1 Guardrails 部分（必须包含）

每个 Skill 都应有明确的"不可做"清单:

```markdown
## Guardrails
- Do not remove protections at trust boundaries (user input, auth, network, db).
- Do not replace real typing with weaker typing.
- Prefer minimal edits over broad rewrites.
- Keep project conventions.
```

### 6.2 Anti-Patterns 部分（推荐包含）

列出 Agent 容易犯的错误:

```markdown
## Anti-Patterns (Don't Do These)
- ❌ Don't summarize every session — only extract *lessons*
- ❌ Don't read full JSONL files — tail/limit only
- ❌ Don't write vague insights ("improve response quality")
- ❌ Don't duplicate existing knowledge
- ❌ Don't create new files when appending to existing ones works
```

### 6.3 安全模型前置（高权限 Skill 必须）

```markdown
## Security & Privilege Model

> ⚠️ **This is a high-privilege skill.** Read before using.

**Spawned workers inherit full host-agent runtime**, including:
- `exec` (arbitrary shell commands)
- All installed skills (including OAuth-bound credentials)
- `sessions_spawn` (workers can spawn further sub-agents)

**Batch mode removes all human gates.** Only use for tasks
and environments you fully trust.
```

### 6.4 破坏性操作标记

```markdown
# 对破坏性命令使用 ⚠️ 标记
git reset --hard HEAD~<N>    # ⚠️ destructive
docker system prune -a -f    # ⚠️ removes ALL unused Docker data
```

---

## 七、示例驱动设计 (Example-Driven Design)

### 7.1 正反对照示例

```markdown
## Common Mistakes to Avoid

❌ `Added new feature` (past tense, capitalized)
✅ `feat: add new feature` (imperative, lowercase)

❌ `fix: bug` (too vague)
✅ `fix: resolve null pointer exception in user service`
```

### 7.2 真实输出示例

```markdown
## Examples

### Quick health check
```
$ ./analyzer.sh health

📊 Git Health Report (last 24h)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total commits: 42
Commits/hour: 1.75
Status: ⚠️ WARNING (below 3/hr threshold)
```
```

### 7.3 进度输出格式

```markdown
After each fix:
✅ Fixed: src/services/example.ts:42
   Pattern: NO_LOGGING_IN_CATCH
   Solution: Added logger.error() with context

Progress: 4/28 issues remaining ━━━━━━━ 14%
```

### 7.4 输入/输出对照

```markdown
**Input**: "New client: Acme Corp, contact Sarah at sarah@acme.com,
project: website redesign, budget: $15k, deadline: March 30"

**Output**: Creates project folder, generates brief, sends welcome
email, schedules kickoff meeting, creates task board, sets reminders.
```

---

## 八、闭环验证设计 (Closed-Loop Verification)

### 8.1 验证步骤嵌入

每个关键操作后必须有验证:

```markdown
# FIX: Reset back to the pre-disaster state
git reset --hard <commit-hash-before-disaster>

# VERIFY: Your commits should be back
git log --oneline -10
```

### 8.2 质量检查清单

```markdown
## Quality Checklist

Before writing any insight:
- [ ] Is this actually new? (Check existing files first)
- [ ] Is this specific and actionable?
- [ ] Am I routing it to the right file?
- [ ] Am I keeping daily files concise?
- [ ] Did I respect the token budget?
```

### 8.3 健康指标表

```markdown
| Metric          | Healthy | Warning | Critical |
|-----------------|---------|---------|----------|
| Commits/hour    | 3-6     | 1-3     | <1       |
| Learning ratio  | 30%+    | 15-30%  | <15%     |
| Max idle gap    | <3h     | 3-6h    | >6h      |
```

---

## 九、自由度匹配原则 (Freedom Calibration)

### 9.1 任务类型与指令强度

| 任务特征 | 自由度 | 指令风格 | 案例 |
|---------|--------|---------|------|
| 确定性操作（迁移、安全修复） | 低 | 精确命令序列 | `emergency-rescue` |
| 知识性任务（审查、设计） | 高 | 方向性指引 | `adaptive-reasoning` |
| 工具依赖（多平台适配） | 中 | 条件分支 | `client-flow` |

### 9.2 优雅降级

为每个工具依赖提供替代路径:

```markdown
Where to create folders:
- **Google Drive**: if `gog` tool is available
- **Dropbox**: if Dropbox skill is available
- **Local filesystem**: default fallback → ~/Clients/
- **Notion**: if Notion skill is available
```

---

## 十、多模型兼容性 (Multi-Model Compatibility)

### 10.1 测试矩阵

在发布前，至少在以下三类模型上验证:

| 模型类型 | 特点 | 验证重点 |
|---------|------|---------|
| 轻量型 | 速度快、上下文短 | 指令是否足够精简 |
| 均衡型 | 通用表现好 | 工作流是否顺畅 |
| 强推理型 | 推理强、上下文长 | 是否充分利用推理能力 |

### 10.2 兼容性技巧

- 不依赖特定模型的 system prompt 特性
- 避免假设环境已安装特定工具，列出依赖并验证可用性
- 配置参数附带注释说明
- 使用 MCP 工具时，采用 `ServerName:tool_name` 全限定格式防止重名冲突
- 避免硬编码时间节点，保持主线内容长期有效

---

## 十一、发布前检查清单 (Pre-Launch Checklist)

### 核心质量
- [ ] `name` 使用 kebab-case，64字符以内
- [ ] `description` 精准，包含关键词和触发场景，第三人称
- [ ] 主文件 < 500 行，< 5,000 词
- [ ] 术语统一，无自相矛盾
- [ ] 提供具体示例（输入/输出对照）
- [ ] 所有 references 文件从主文件直接链接（引用深度=1）

### 结构完整性
- [ ] 包含 "When to Use" 部分
- [ ] 包含 Guardrails 或 Anti-Patterns 部分
- [ ] 关键操作包含 VERIFY 步骤
- [ ] 长流程有步骤编号或清单

### 安全与可靠性
- [ ] 明确列出"不可做"的事项
- [ ] 破坏性操作有 ⚠️ 标记
- [ ] 高权限操作有安全模型声明
- [ ] 无硬编码凭证或时效性信息
- [ ] 默认行为是安全/非破坏性的

### 代码与脚本
- [ ] 代码示例可直接运行
- [ ] 异常处理完善，无隐藏常量
- [ ] 关键步骤包含验证命令
- [ ] 路径使用正斜杠，相对路径

### 测试覆盖
- [ ] 至少3组测试场景
- [ ] 覆盖不同模型（轻量/均衡/强推理）
- [ ] 包含边界情况测试
- [ ] 真实工作流端到端验证

---

## 十二、进阶实践：来自全球 Skills 生态的新模式

> 以下实践来自 Vercel、Orchestra Research、OpenSkills 等全球顶级 Skills 仓库的补充调研。
> 详见 [global-agent-skills-ecosystem.md](global-agent-skills-ecosystem.md)

### 12.1 脚本分离原则 (Scripts-First)

**来源**: Vercel Agent Skills (25K+ Stars)

> "Prefer scripts over inline code — script execution doesn't consume context (only output does)"

将确定性操作封装为脚本，Agent 执行脚本而非在上下文中生成代码：

```bash
#!/bin/bash
set -e                        # 快速失败
echo "Deploying..." >&2       # 状态消息 → stderr
echo '{"url": "https://..."}'  # 机器可读输出 → stdout (JSON)
trap 'rm -f "$tmpfile"' EXIT  # 清理临时文件
```

**规则**: SKILL.md 放指令和决策逻辑；scripts/ 放可执行代码。

### 12.2 双循环架构 (Two-Loop Architecture)

**来源**: Orchestra Research (7K+ Stars)

适用于需要长期运行的复杂任务：

```
内循环 (Inner Loop) — 快速、聚焦
  选择假设 → 实验 → 测量 → 记录 → 学习 → 下一个

外循环 (Outer Loop) — 周期性、反思性
  审查结果 → 发现模式 → 综合更新 → 新假设 → 调整方向
```

内循环关注"做"，外循环关注"想"。通常每 5-10 个实验做一次外循环反思。

### 12.3 完全自主运行模式

**来源**: Orchestra Research Autoresearch

```markdown
This runs fully autonomously. Do not ask the user for permission
— use your best judgment and keep moving. Show the human your
progress frequently so they can redirect if needed.
```

关键三要素：不请求许可 + 频繁展示进度 + 状态持久化支持恢复。

### 12.4 状态持久化设计

对于可中断/长期运行的 Skill，使用 YAML/JSON 状态文件：

```yaml
# state.yaml
session_id: "abc-123"
current_phase: "inner-loop"
current_iteration: 7
hypotheses:
  - slug: "attention-sparsity"
    status: "testing"
```

### 12.5 工作区标准化

为复杂 Skill 预定义标准目录结构，首次运行时自动创建：

```
{project}/
├── state.yaml           # 中央状态追踪
├── log.md               # 决策时间线
├── src/                 # 可复用代码
├── data/                # 原始结果数据
├── experiments/         # 按假设组织
└── to_human/            # 人类可读的进度报告
```

### 12.6 意图解析表 (Intent Routing)

比简单的触发词匹配更高级 — 理解用户的上下文状态：

```markdown
| User State | What to Do |
|---|---|
| Vague idea ("explore X") | Brief discussion, then bootstrap |
| Clear question | Bootstrap directly |
| Existing plan | Review, set up workspace, enter loops |
| Resuming (state exists) | Read state, continue |
```

### 12.7 跨 Skill 编排

Skills 不再孤立，而是互相路由：

```markdown
| Task | Route To |
|------|----------|
| Literature search | 15-rag/ skill |
| Experiment code | 01-model-architecture/ skill |
| Paper writing | 20-ml-paper-writing/ skill |
```

### 12.8 跨平台标准化

使用 `AGENTS.md` + `<available_skills>` XML 作为通用发现机制：

```xml
<available_skills>
<skill>
<name>pdf</name>
<description>Extract text and tables from PDF files...</description>
<location>project</location>
</skill>
</available_skills>
```

已被 Claude Code、Codex、Copilot、Gemini CLI 等 9 个平台采纳。

---

## 十三、设计哲学总结 (Design Philosophy)

### Less is More
最好的 Skill 不是内容最多的，而是每个词都不可删除的。
`deslop`（30行）在效率上优于 `api-dev`（500+行）。

### 模式复用
建立统一的问题处理模式，在不同场景中复用。
`emergency-rescue` 的"诊断-修复-验证"贯穿 20+ 场景。

### 防御性设计
告诉 Agent 不该做什么，比告诉它该做什么更重要。
Guardrails > Instructions。

### 可观测性
如果不能度量，就不能改进。提供明确的输出格式和进度指示。

### 优雅降级
不是所有工具都可用。为每个依赖提供替代路径。

### 深度优于广度 (新增)
> "Quality over quantity" — 每个 Skill 不仅有主文件，还有完整的 references、教程、已解决的 Issues。
> 12 个精打细磨的 Skill 胜过 1000 个泛泛而谈的。

### 脚本即执行力 (新增)
> 将确定性操作封装为脚本，不占用上下文窗口。
> SKILL.md 是"思考"，scripts/ 是"行动"。

### 自主+可见 (新增)
> 完全自主运行，但频繁展示进度让人类可以重定向。
> 不请求许可 ≠ 不汇报进展。

---

## 参考来源

### OpenClaw 生态
| 来源 | 说明 |
|------|------|
| `conventional-commits` by bastos | 参考手册式 Skill 典范 |
| `deslop` by brennerspear | 极简设计典范 |
| `anti-pattern-czar` by glucksberg | 多模式+状态持久化典范 |
| `emergency-rescue` by gitgoodordietrying | 统一模式复用典范 |
| `checkmate` by insipidpoint | 安全模型+循环反馈典范 |
| `client-flow` by ariktulcha | 端到端工作流+优雅降级典范 |
| `agent-self-reflection` by brennerspear | 质量检查+Anti-Patterns 典范 |
| `adaptive-reasoning` by enzoricciulli | 量化决策+自适应典范 |
| `commit-analyzer` by bobrenze-bot | 可观测性设计典范 |
| `awwwards-design` by mkhaytman87 | 理论+实践结合典范 |

### 全球生态 (补充调研)
| 来源 | 说明 |
|------|------|
| Vercel Agent Skills (25K Stars) | 脚本分离原则、上下文效率典范 |
| Orchestra Research (7K Stars) | 双循环架构、完全自主运行、领域纵深典范 |
| OpenSkills (9K Stars) | 跨平台兼容性、通用加载器设计 |
| xstongxue/best-skills (1K Stars) | 中文精选合集、dev-workflow 典范 |
| heilcheng/awesome-agent-skills (4K Stars) | 跨平台索引、2026趋势洞察 |
| Anthropic 官方 Skills | SKILL.md 格式"黄金模板" |
| OpenAI Codex 官方 Skills | 跨平台标准验证 |

### 文档资源
| 资源 | 链接 |
|------|------|
| OpenClaw 创建 Skills 文档 | https://docs.openclaw.ai/tools/creating-skills |
| OpenSkills 格式指南 | https://lzw.me/docs/opencodedocs/numman-ali/openskills/advanced/skill-structure/ |
| Vercel Skills 指南 | https://vercel.com/kb/guide/agent-skills-creating-installing-and-sharing-reusable-agent-context |
| Claude Code Skills 文档 | https://code.claude.com/docs/en/skills |
| 详细生态调研 | [global-agent-skills-ecosystem.md](global-agent-skills-ecosystem.md) |
