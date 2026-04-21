# Chapter 7: 渐进式加载

> **Motto**: "上下文是公共资源，每个 Token 都很宝贵"

> 随着 Skill 越来越复杂——命令多了、示例多了、模板多了——SKILL.md 膨胀到了 500 行甚至更多。一次性加载这么多内容，会吃掉宝贵的上下文空间。本章你将学会三层架构，让 Skill 像图书馆一样组织知识：目录在手边，详细资料在书架上。

![Chapter 7: 渐进式加载](images/ch07-progressive-loading.png)

## The Problem

你的 `test-writer` Skill 在第 6 章加了示例和模板后，已经有 200 行了。现在你想为它增加：
- 针对不同框架（pytest, unittest, jest）的模板
- 常见测试模式的参考手册（mock 指南、fixture 用法、参数化测试）
- 一个分析代码复杂度的 Python 脚本

如果把这些全部塞进 SKILL.md，文件会超过 800 行（约 8000 tokens）。加载后，它会占用 Agent 上下文窗口的一大块——让留给实际对话的空间变小。

## The Solution

**三层架构**把 Skill 的内容分散到多个文件中，按需加载：

```
refactor-guide/
├── SKILL.md                    ← Layer 1+2: 核心指令（< 300 行）
├── scripts/
│   └── analyze_complexity.py   ← Layer 3: 确定性脚本
└── reference/
    ├── refactoring-patterns.md ← Layer 3: 参考文档
    └── code-smells.md          ← Layer 3: 参考文档
```

**Layer 1**（~100 tokens）：YAML Frontmatter 中的 name + description，始终在上下文中。

**Layer 2**（~2000-5000 tokens）：SKILL.md 正文，Agent 决定加载时读入。这里放核心指令、命令表、最重要的示例。

**Layer 3**（按需）：辅助文件。Agent 在执行过程中，根据 SKILL.md 中的引用，按需读取特定文件。

关键原则：**SKILL.md 只放"必须知道的"，辅助文件放"需要时再看的"。**

## 7.1 什么放 SKILL.md，什么放辅助文件

| 内容类型 | 放在哪里 | 原因 |
|---------|---------|------|
| 命令表 | SKILL.md | Agent 需要第一时间知道有哪些命令 |
| 核心执行步骤 | SKILL.md | 每次执行都需要 |
| 1-2 个关键示例 | SKILL.md | 锚定基本行为 |
| 全局约束 | SKILL.md | 每次执行都需要 |
| 详细的参考文档 | reference/ | 只在特定场景需要 |
| 大量的示例库 | reference/ | 按需查阅 |
| HTML 模板 | templates/ | Agent 渲染时读取 |
| 计算脚本 | scripts/ | Agent 需要确定性计算时执行 |
| 配置文件 | assets/ | 运行时读取 |

## 7.2 引用辅助文件

在 SKILL.md 中，用相对路径的 Markdown 链接引用辅助文件。Agent 会在需要时用 Read 工具读取：

```markdown
## 重构模式

常见的重构模式和代码异味列表见 [refactoring-patterns.md](reference/refactoring-patterns.md)。
执行重构前，先参考 [code-smells.md](reference/code-smells.md) 识别问题。
```

更强的引导方式——用 `Study` 关键词明确告诉 Agent 去阅读：

```markdown
### Pass 1 — 分析代码

Study [refactoring-patterns.md](reference/refactoring-patterns.md) 了解常见的重构模式，
然后分析目标代码中存在的问题。
```

> **Tip**: "Study" 这个词比 "see" 或 "refer to" 更强——它暗示 Agent 应该在执行之前读取并理解文件内容。

## 7.3 scripts/ 目录设计：脚本优先原则

当任务需要**确定性计算**（数学运算、数据转换、文件处理）时，用脚本比让 LLM 做更可靠。

但脚本的价值不仅是可靠性——还有一个容易被忽略的关键洞察：

> **脚本执行不消耗上下文窗口。只有脚本的输出（stdout）进入上下文。**

这意味着什么？假设你有一个 200 行的数据处理逻辑。如果写在 SKILL.md 中，Agent 每次加载 Skill 都会把这 200 行读入上下文。但如果封装为脚本：

- 脚本代码本身不占上下文（Agent 不需要"阅读"脚本来执行它）
- Agent 只需要知道"运行 `python scripts/process.py`"——一行指令
- 脚本的 stdout 输出（通常几十行 JSON）进入上下文

200 行代码变成了 1 行指令 + 几十行输出。这就是 **Scripts-First 原则**——确定性操作应该尽可能封装为脚本。

### Vercel 的脚本规范

Vercel Agent Skills（25K+ Stars）为脚本制定了一套严格的规范，值得借鉴：

```bash
#!/bin/bash
set -e                         # 快速失败——任何命令出错立即退出
echo "Processing..." >&2       # 状态消息 → stderr（不进入 Agent 上下文）
echo '{"result": "success"}'   # 机器可读输出 → stdout（进入上下文，JSON 格式）
trap 'rm -f "$tmpfile"' EXIT   # 清理临时文件——即使出错也执行
```

四条规则：
1. **`set -e`**：快速失败，不要在错误后继续执行
2. **stderr 用于状态消息**：Agent 不需要看到 "Processing..."，人类可以在终端看到
3. **stdout 用于机器可读输出**：JSON 格式，Agent 可以直接解析
4. **`trap` 清理**：即使脚本出错也要清理临时文件

### Python 脚本示例

```python
# scripts/analyze_complexity.py
"""分析 Python 文件的代码复杂度。"""
import ast
import sys
import json


def analyze_file(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read())
    
    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = _calculate_complexity(node)
            results.append({
                "name": node.name,
                "line": node.lineno,
                "complexity": complexity,
                "recommendation": "refactor" if complexity > 10 else "ok"
            })
    return results


def _calculate_complexity(node):
    """计算圈复杂度。"""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


if __name__ == "__main__":
    filepath = sys.argv[1]
    results = analyze_file(filepath)
    json.dump(results, sys.stdout, indent=2)
```

脚本设计规范总结：

1. **JSON 输出到 stdout**：Agent 可以直接解析
2. **状态/调试信息到 stderr**：不进入 Agent 上下文
3. **参数通过命令行传入**：`python scripts/analyze_complexity.py target.py`
4. **错误用非零退出码**：Agent 可以检测执行是否成功
5. **`set -e` + `trap`**：快速失败 + 清理资源

### 什么适合封装为脚本

| 适合封装 | 不适合封装 |
|---------|-----------|
| 数据解析、格式转换 | 需要 LLM 判断的决策 |
| 数学计算、统计聚合 | 需要理解上下文的操作 |
| 文件系统批量操作 | 需要和用户交互的步骤 |
| API 调用和数据获取 | 创意性内容生成 |

经验法则：如果操作**不需要"思考"**（用 if/else 就能覆盖所有分支），就封装为脚本。

在 SKILL.md 中引用脚本：

```markdown
### Pass 1 — 代码复杂度分析

运行复杂度分析脚本：
```bash
python scripts/analyze_complexity.py <target_file>
```

脚本输出 JSON 格式的函数复杂度列表。对 complexity > 10 的函数重点分析。
```

## 7.4 实战：refactor-guide Skill 的三层架构

```markdown
---
name: refactor-guide
description: 指导代码重构。分析代码复杂度和异味，推荐重构模式，生成重构计划。当用户想重构代码或改善代码质量时使用。
---

# Refactor Guide

分析代码质量问题并生成重构计划。

## Commands

| Command | Purpose |
|---------|---------|
| `/refactor-guide analyze <file>` | 分析代码问题 |
| `/refactor-guide plan` | 基于分析生成重构计划 |
| `/refactor-guide execute` | 按计划执行重构 |

## `/refactor-guide analyze <file>`

### 执行步骤

1. 运行 `python scripts/analyze_complexity.py <file>` 获取复杂度数据
2. 读取目标文件
3. 参考 [code-smells.md](reference/code-smells.md) 检查常见代码异味
4. 输出分析报告，包含：
   - 复杂度评分（脚本输出）
   - 发现的代码异味列表
   - 严重度排序

## `/refactor-guide plan`

### 执行步骤

1. 读取上一步的分析报告
2. 参考 [refactoring-patterns.md](reference/refactoring-patterns.md) 匹配重构模式
3. 为每个问题推荐具体的重构手法
4. 输出重构计划：按优先级排列，每步描述改动范围和预期效果

## 约束

- 每次重构只修改一个问题——不要一次性改太多
- 重构前确认有测试覆盖——没有测试的代码先写测试
- 重构不改变外部行为——这是重构的定义
```

目录结构：

```
refactor-guide/
├── SKILL.md                          ← 80 行核心指令
├── scripts/
│   └── analyze_complexity.py         ← 确定性复杂度计算
└── reference/
    ├── refactoring-patterns.md       ← 20 种重构模式参考
    └── code-smells.md                ← 常见代码异味清单
```

SKILL.md 只有 80 行，但通过引用辅助文件，Skill 的知识深度远超 80 行。

## 7.5 案例解剖：tech-book-writer 的完整三层架构

```
tech-book-writer/
├── SKILL.md                      ← 500 行：命令表 + 核心方法论
├── progressive-methodology.md    ← 渐进式教学法详解
├── style-guide.md                ← O'Reilly 写作风格规范
├── illustration-guide.md         ← 三层插图系统
├── bilingual-guide.md            ← 双语翻译规则
├── pdf-pipeline.md               ← PDF 构建管线
├── templates/
│   ├── cover-template.md         ← 封面 prompt 模板
│   ├── pandoc-metadata.yaml      ← Pandoc 配置
│   └── weasyprint-style.css      ← 排版样式
└── scripts/
    ├── build_pdf_weasyprint.py   ← WeasyPrint PDF 构建
    ├── build_pdf_pandoc.py       ← Pandoc PDF 构建
    ├── init_book.py              ← 初始化书籍目录
    └── analyze_book.py           ← 书籍分析工具
```

设计决策分析：

- **SKILL.md 放什么**：命令表（14 个命令的索引）、章节骨架格式、Review checklist、关键约束。这些是**每次执行都需要**的信息。

- **辅助 .md 放什么**：详细的方法论说明、风格指南、翻译规则。这些只在对应命令执行时才需要——写章节时需要 style-guide.md，翻译时需要 bilingual-guide.md。

- **scripts/ 放什么**：PDF 构建、书籍分析。这些是**确定性操作**——不需要 LLM 判断，直接执行脚本更可靠。

- **templates/ 放什么**：CSS 样式、YAML 配置。这些是**静态资源**——内容不变，被脚本或渲染工具直接使用。

## 7.6 何时需要三层架构

不是所有 Skill 都需要三层架构。判断标准：

| SKILL.md 行数 | 建议 |
|---------------|------|
| < 100 行 | 单文件足够 |
| 100-300 行 | 考虑分离，但不强制 |
| 300-500 行 | 应该分离参考文档和模板 |
| > 500 行 | 必须分离，SKILL.md 只保留核心 |

简单 Skill（如 `quick-fix`、`commit-message`）不需要三层架构——过度拆分反而增加复杂性。

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 所有内容塞在一个 SKILL.md | 三层架构分散知识 |
| Skill 越复杂文件越大 | SKILL.md 保持精简，深度知识按需加载 |
| 没有脚本支持 | scripts/ 提供确定性计算 |
| 不知道脚本比内联代码好在哪 | 理解 Scripts-First 原则——脚本不消耗上下文 |

**Cumulative capability**: 你的 `refactor-guide` Skill 使用了三层架构（80 行 SKILL.md + 脚本 + 参考文档），知识深度远超一个文件能承载的。

## Try It Yourself

> 完整代码见 `code/track-1/ch07-refactor-guide/`（含 scripts/ + reference/），可直接复制到 `~/.qoder/skills/` 使用。
>
> **Track 2 演进**：对比 `code/track-2/v06-examples/` 和 `code/track-2/v07-architecture/` 的 diff，
> 观察三层架构拆分如何从 202 行变为 229 行 + scripts/ + reference/。

1. **Verify**: 构建 `refactor-guide` Skill 的完整三层结构，测试 `analyze` 命令。
2. **Extend**: 把 Chapter 6 的 `test-writer` 重构为三层——把大量示例移到 `reference/examples.md`，SKILL.md 只保留 1 个关键示例。
3. **Explore**: 计算你已有的每个 Skill 的 SKILL.md 行数。哪些超过了 300 行？设计它们的分离方案。
4. **Scripts-First**: 找出你的 Skill 中一段可以封装为脚本的逻辑（数据处理、格式转换等），把它从 SKILL.md 的自然语言描述改为 scripts/ 中的可执行脚本。对比上下文消耗的变化。

## Summary

- **三层架构**：SKILL.md（核心指令）+ scripts/（确定性脚本）+ reference/（参考文档）
- **Scripts-First 原则**：脚本执行不消耗上下文，只有输出进入上下文——确定性操作应尽可能封装为脚本
- SKILL.md 只放**每次执行都需要**的内容，其余按需引用
- 用 `Study [file](path)` 引导 Agent 读取辅助文件
- 脚本规范：JSON→stdout, 状态→stderr, `set -e` 快速失败, `trap` 清理资源
- **300 行**是分离阈值——超过就应该拆分

## Further Reading

- 第 4 章回顾：交接文件也是一种"层"——Multi-Pass 的每个 Pass 输出就像临时的 reference/
- 操作系统的虚拟内存：不是所有数据都需要在内存中——三层架构的灵感来源
- 第 8 章《多工具编排》——scripts/ 中的脚本如何与 Agent 的工具协作
- Vercel Agent Skills 指南——Scripts-First 原则的来源
