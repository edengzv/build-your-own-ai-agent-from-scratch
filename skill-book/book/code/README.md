# 代码示例 — 双轨并行架构

本目录包含全书所有可运行的代码示例，采用**双轨并行**架构。

## 如何使用

### Track 1: 每章独立 Skill (`track-1/`)

每章产出的代表性 Skill，完整、独立、可直接使用。

**使用方式**：复制任意 Skill 目录到 `~/.qoder/skills/`（或 `~/.claude/skills/`），重启 Agent 即可使用。

| 目录 | Skill | 行数 | 核心技巧 |
|------|-------|------|---------|
| ch01-quick-fix/ | quick-fix | ~10 | 最小结构 |
| ch02-code-review/ | code-review | ~30 | 精准 description |
| ch03-commit-message/ | commit-message | ~50 | 五要素 + Explain Why |
| ch04-api-doc-writer/ | api-doc-writer | ~100 | Multi-Pass 工作流 |
| ch05-project-scaffold/ | project-scaffold | ~120 | 命令路由 |
| ch06-test-writer/ | test-writer | ~150 | 示例锚定 + 模板 |
| ch07-refactor-guide/ | refactor-guide | ~200 | 三层架构 + 脚本优先 |
| ch08-deploy-checker/ | deploy-checker | ~250 | 多工具编排 |
| ch09-pr-reviewer/ | pr-reviewer | ~200 | Checklist + Guardrails |
| ch10-eval/ | (评估材料) | — | 断言配置 + 优化模板 |
| ch11-analysis/ | (分析材料) | — | 7 维度解剖模板 |
| ch12-skill-creator/ | skill-creator | ~320 | 元技能（= Track 2 v12） |

### Track 2: skill-creator 渐进演进 (`track-2/`)

一个 Skill 从 v01（10 行）进化到 v12（320 行）的完整过程。每个版本只新增该章教授的技巧，让你看到技巧的**累积效果**。

**使用方式**：对比相邻版本的 diff，理解每项技巧如何改进 Skill。只有 v12 是生产级——其余版本仅供学习。

```bash
# 对比两个版本的差异
diff track-2/v03-five-elements/SKILL.md track-2/v04-multi-pass/SKILL.md
```

### 与章节正文的关系

- 章节正文中的代码片段是**教学用的局部示例**（可能省略部分内容以突出重点）
- 本目录中的代码是**完整可运行版本**
- 章节末尾会用 `> 完整代码见 code/track-1/chXX-xxx/` 引用本目录

### Ch10/Ch11 特殊说明

这两章不产出新 Skill，但提供：
- Ch10: 评估配置、测试用例模板、Description 优化循环日志
- Ch11: 7 维度分析模板、案例分析报告

## 快速开始

1. **想学某项技巧？** → 读对应章节 + 查看 `track-1/` 中的完整 Skill
2. **想理解技巧累积效果？** → 对比 `track-2/` 的相邻版本
3. **想直接用？** → 复制 `track-1/` 中任意 Skill 到 skills 目录
4. **想要最强的 skill-creator？** → 直接用 `track-2/v12-final/`

## 环境要求

- 任意支持 SKILL.md 的 Agent 工具（Qoder / Claude Code / Cursor）
- Ch7+ 的 scripts/ 需要 Python 3.10+ 和 Bash
