# Chapter 8: 多工具编排

> **Motto**: "Skill 的力量不在文字，在于它能调动的工具"

> 到目前为止，你的 Skill 主要是"知识型"的——告诉 Agent 怎么思考和输出。但强大的 Skill 还能指导 Agent 按特定顺序使用工具：先用 Bash 检查环境，再用 Read 读取配置，接着用 WebFetch 验证服务。本章你将学会在 Skill 中编排多工具协作。

![Chapter 8: 多工具编排](images/ch08-multi-tool-orchestration.png)

## The Problem

你想写一个部署检查 Skill。检查流程是：

1. 检查 Git 工作区是否干净
2. 运行测试套件
3. 验证环境变量配置
4. 检查依赖版本
5. 验证健康检查端点

每个步骤需要不同的工具：Bash（git status, npm test）、Read（.env 文件）、WebFetch（健康检查）。如果只写"检查部署就绪状态"，Agent 会自己决定执行顺序——可能会在测试失败后还继续检查环境变量，浪费时间。

## The Solution

**工具编排**是在 Skill 中明确声明每个步骤使用什么工具、按什么顺序、在什么条件下执行。

## 8.1 Tool Usage 声明

在 SKILL.md 中用表格声明 Skill 需要的工具：

```markdown
## Tool Usage

| Tool | Purpose |
|------|---------|
| Bash | 运行 git status, npm test, 检查环境 |
| Read | 读取 .env, package.json 配置文件 |
| WebFetch | 验证健康检查端点 |
| Write | 输出检查报告 |
```

这个声明不是限制——Agent 仍然可以用任何工具。但它为 Agent 提供了**工具使用指南**，让 Agent 在正确的步骤使用正确的工具。

## 8.2 编排模式

### 模式 1: 管线模式（Pipeline）

步骤严格按序执行，前一步的输出是后一步的输入：

```markdown
## 执行步骤

1. **[Bash]** 运行 `git status --porcelain`
   - 如果输出不为空，报告"工作区不干净"并标记为 FAIL
   - 将结果记录到检查报告

2. **[Bash]** 运行 `npm test --silent`
   - 如果退出码非零，报告"测试失败"并标记为 FAIL
   - 记录失败的测试用例

3. **[Read]** 读取 `.env` 和 `.env.example`
   - 对比两个文件，检查是否有缺失的环境变量
   - 标记缺失的变量为 WARNING

4. **[Read]** 读取 `package.json`
   - 检查 dependencies 中是否有 deprecated 包
   
5. **[WebFetch]** 请求健康检查端点 (如果有配置)
   - 验证返回 200 状态
   
6. **[Write]** 输出完整的检查报告到 `deploy-check-report.md`
```

### 模式 2: 条件模式

根据中间结果选择不同路径：

```markdown
## 条件分支

如果 Step 1 (git status) 为 FAIL：
  → 停止检查，输出"请先提交或暂存所有改动"
  → 不执行后续步骤

如果 Step 2 (tests) 为 FAIL：
  → 继续后续检查，但在最终报告中标记为"阻塞部署"
  → 建议用户先修复测试

如果所有步骤 PASS：
  → 输出"部署就绪 ✓"
```

### 模式 3: 错误恢复模式

当工具调用失败时的处理策略：

```markdown
## 错误处理

- 如果 `npm test` 命令不存在（不是 Node 项目），跳过测试步骤
- 如果 `.env` 文件不存在，标记为 WARNING 而非 FAIL
- 如果健康检查端点超时，标记为 WARNING 并建议手动检查
- 如果任何工具调用异常，记录错误信息到报告，继续后续步骤
```

## 8.3 完整的 deploy-checker Skill

````markdown
---
name: deploy-checker
description: 检查应用的部署就绪状态。验证 Git 工作区、测试、环境变量、依赖和健康检查。当用户准备部署或想确认部署条件时使用。
---

# Deploy Checker

在部署前自动检查所有前置条件，生成部署就绪报告。

## Commands

| Command | Purpose |
|---------|---------|
| `/deploy-checker check` | 运行完整的部署前检查 |
| `/deploy-checker check --quick` | 只检查 git 和 tests |
| `/deploy-checker report` | 查看上次检查报告 |

## Tool Usage

| Tool | Purpose |
|------|---------|
| Bash | 运行 git status, test suite, 环境检查 |
| Read | 读取配置文件 (.env, package.json, etc.) |
| WebFetch | 验证健康检查端点 |
| Write | 输出检查报告 |

## `/deploy-checker check`

### Step 1: Git 工作区检查 [Bash]

运行 `git status --porcelain`

| 结果 | 状态 | 动作 |
|------|------|------|
| 输出为空 | PASS | 继续 |
| 有未提交改动 | FAIL | 停止，提示用户先提交 |
| 不是 git 仓库 | SKIP | 继续，记录 warning |

### Step 2: 测试套件 [Bash]

检测项目类型并运行对应的测试命令：

| 检测文件 | 测试命令 |
|---------|---------|
| package.json | `npm test` |
| pyproject.toml / setup.py | `pytest` |
| Cargo.toml | `cargo test` |
| go.mod | `go test ./...` |

如果未检测到项目类型，标记为 SKIP。

### Step 3: 环境变量 [Read]

1. 读取 `.env.example`（或 `.env.template`）
2. 读取 `.env`
3. 对比：`.env.example` 中有但 `.env` 中没有的变量标记为 WARNING

### Step 4: 依赖检查 [Read + Bash]

1. 读取依赖配置文件
2. 运行 `npm audit --json` 或 `pip audit --format json`（如果可用）
3. 高危漏洞标记为 FAIL，中低危标记为 WARNING

### Step 5: 健康检查 [WebFetch]（可选）

如果项目中有 `docker-compose.yml` 或配置文件中定义了健康检查 URL：
1. 请求健康检查端点
2. 验证返回 200 状态

如果没有健康检查配置，标记为 SKIP。

### 输出报告 [Write]

输出到 `deploy-check-report.md`：

```
# 部署检查报告

时间: {timestamp}
项目: {project_name}

## 检查结果

| # | 检查项 | 状态 | 详情 |
|---|--------|------|------|
| 1 | Git 工作区 | PASS/FAIL/SKIP | ... |
| 2 | 测试套件 | PASS/FAIL/SKIP | ... |
| 3 | 环境变量 | PASS/WARNING/SKIP | ... |
| 4 | 依赖安全 | PASS/WARNING/SKIP | ... |
| 5 | 健康检查 | PASS/WARNING/SKIP | ... |

## 总结

{总体评估: 部署就绪 / 有阻塞问题 / 有警告}

## 建议

{如果有 FAIL 或 WARNING，列出具体的修复建议}
```

## 约束

- 不要自动修复任何问题——只报告和建议
- FAIL 状态表示必须修复才能部署
- WARNING 状态表示建议修复但不阻塞
- SKIP 状态表示该检查不适用于当前项目
````

## 8.4 案例解剖：wechat-article-writer 的工具编排

`wechat-article-writer` 在 5 个 Pass 中使用了 5 种不同的工具：

```
Pass 1 [WebFetch] → 抓取英文原文
Pass 2 [—]        → 纯分析，不需要工具
Pass 3 [Write]    → 输出文章 Markdown
Pass 4 [ImageGen] → 生成封面和配图
Pass 5 [show_widget + Write] → 渲染预览 + 输出 HTML
```

工具选择的逻辑：

- **WebFetch** 只在 Pass 1 使用——因为只有第一步需要从外部获取数据
- **ImageGen** 只在 Pass 4 使用——配图制作和写作完全分离
- **show_widget** 只在 Pass 5 使用——预览是最后一步

关键设计：**AskUserQuestion 作为编排中的"人工检查点"**——Pass 1 后和 Pass 2 后各有一次用户确认，确保方向正确再继续使用工具。

## 8.5 工具编排的注意事项

### 声明工具但不限制工具

```markdown
# 好：声明用途，让 Agent 灵活判断
## Tool Usage
| Tool | Purpose |
|------|---------|
| Bash | 运行测试和 Git 命令 |

# 坏：过度限制
仅使用 Bash 工具，不要使用其他任何工具。
```

### 处理工具不可用的情况

```markdown
# 好：有降级策略
如果 WebFetch 不可用或超时，跳过健康检查步骤，标记为 SKIP。

# 坏：假设工具总是可用
必须用 WebFetch 检查健康端点。  # 如果没有网络呢？
```

### 明确工具调用的参数

```markdown
# 好：具体的命令
运行 `git diff --cached --stat`

# 坏：模糊的指令
用 Git 看看有什么改动
```

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| Skill 只提供知识 | Skill 能编排多种工具协作 |
| 工具使用顺序由 Agent 自行决定 | 明确的步骤 + 工具映射 |
| 没有错误处理策略 | 条件分支 + 降级策略 |

**Cumulative capability**: 你的 `deploy-checker` Skill 编排了 4 种工具（Bash, Read, WebFetch, Write），能在部署前自动检查 5 个维度。

## Try It Yourself

> 完整代码见 `code/track-1/ch08-deploy-checker/`（含 scripts/ + reference/），可直接复制到 `~/.qoder/skills/` 使用。
>
> **Track 2 演进**：对比 `code/track-2/v07-architecture/` 和 `code/track-2/v08-tools/` 的 diff，
> 观察 Tool Usage 表和 Pipeline 编排如何从 229 行扩展到 307 行。

1. **Verify**: 用 `deploy-checker` 检查一个真实项目的部署就绪状态。
2. **Extend**: 给 `api-doc-writer` 添加 Tool Usage 表，明确每个 Pass 使用什么工具。
3. **Explore**: 设计一个需要 3+ 种工具的 Skill 场景（如"竞品分析"：WebSearch 搜索 + WebFetch 抓取 + Write 输出报告），画出工具编排流程图。

## Summary

- 用 **Tool Usage 表**声明 Skill 需要的工具和用途
- 三种编排模式：**管线**（顺序）、**条件**（分支）、**错误恢复**（降级）
- 在步骤中用 **[Tool]** 标记明确每步使用什么工具
- 声明工具但不限制——让 Agent 保持灵活性
- 处理工具不可用的情况——有降级策略

## Further Reading

- 第 7 章回顾：scripts/ 中的脚本也是一种工具——Bash 执行脚本是常见的编排模式
- 第 4 章回顾：Multi-Pass 自然地分离了不同工具的使用阶段
- MCP Server 协议：当内置工具不够时，通过 MCP 扩展工具能力
