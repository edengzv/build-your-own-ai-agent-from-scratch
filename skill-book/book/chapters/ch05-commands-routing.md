# Chapter 5: 命令与路由

> **Motto**: "一个 Skill 多种用法，由命令来切换"

> 到目前为止，每个 Skill 只做一件事。但真实场景中，一个领域的 Skill 可能需要多种操作模式。你不会为"创建项目"、"添加组件"、"查看配置"分别写三个 Skill——它们属于同一个领域，应该是一个 Skill 的不同命令。

![Chapter 5: 命令与路由](images/ch05-commands-routing.png)

## The Problem

你为团队搭建项目模板写了三个 Skill：

```
skills/
├── project-create/    → 创建新项目
├── project-add/       → 添加组件到已有项目
└── project-config/    → 查看和修改项目配置
```

三个 Skill，三个 description，三份维护工作。更糟糕的是，Agent 有时会在"添加组件"的请求中加载了"创建项目"的 Skill——因为它们的 description 太相似了。

另一个问题：你在第 4 章的 `api-doc-writer` 中设计了 3-Pass 工作流。但有时你只想执行 Pass 1（看端点清单），不想走完整个流程。目前你没法做到。

## The Solution

**命令系统**让一个 Skill 暴露多个操作入口。就像 `git` 有 `commit`、`push`、`pull` 多个子命令一样，一个 Skill 可以有 `create`、`add`、`config` 多个命令。

```markdown
## Commands

| Command | Purpose |
|---------|---------|
| `/project-scaffold create <type>` | 创建新项目 |
| `/project-scaffold add <component>` | 添加组件到已有项目 |
| `/project-scaffold config` | 查看当前项目配置 |
```

Agent 看到命令表后，能根据用户的请求自动路由到正确的命令。

## 5.1 命令表的设计

命令表是一个 Markdown 表格，放在 SKILL.md 的开头（description 之后、详细指令之前）：

```markdown
---
name: project-scaffold
description: 创建和管理项目脚手架。支持创建新项目、添加组件、修改配置。当用户需要初始化项目或添加模块时使用。
---

# Project Scaffold

创建和管理标准化的项目结构。

## Commands

| Command | Purpose |
|---------|---------|
| `/project-scaffold create <type>` | 创建新项目（type: api, web, cli, lib） |
| `/project-scaffold add <component>` | 添加组件（auth, database, testing, ci） |
| `/project-scaffold config` | 查看/修改项目配置 |
| `/project-scaffold list` | 列出可用的项目类型和组件 |
```

### 命令命名规范

```
/skill-name verb [argument]
```

- **skill-name**: Skill 的 name 字段
- **verb**: 动词，描述操作
- **argument**: 可选参数

推荐的动词：

| 动词 | 含义 | 示例 |
|------|------|------|
| create | 创建新的 | `/scaffold create api` |
| add | 添加到已有的 | `/scaffold add auth` |
| update | 更新已有的 | `/scaffold update config` |
| check | 检查/验证 | `/scaffold check dependencies` |
| list | 列出可用选项 | `/scaffold list components` |
| preview | 预览结果 | `/scaffold preview` |

## 5.2 命令的详细指令

命令表告诉 Agent 有哪些命令。每个命令的详细执行逻辑放在表格下方的独立章节中：

```markdown
## `/project-scaffold create <type>`

创建一个新项目。

### 支持的项目类型

| type | 描述 | 技术栈 |
|------|------|--------|
| api | REST API 服务 | Python + FastAPI |
| web | 前端 Web 应用 | TypeScript + React |
| cli | 命令行工具 | Python + Click |
| lib | Python 库 | Python + setuptools |

### 执行步骤

1. 如果 `<type>` 未指定，用 AskUserQuestion 询问
2. 创建项目目录结构
3. 生成配置文件（pyproject.toml / package.json）
4. 生成 README.md 模板
5. 初始化 Git 仓库
6. 输出项目结构摘要

### 项目结构（以 api 为例）

my-project/
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── routes/
├── tests/
├── pyproject.toml
├── README.md
└── .gitignore

---

## `/project-scaffold add <component>`

向已有项目添加组件。

### 支持的组件

| component | 添加的内容 |
|-----------|-----------|
| auth | JWT 认证中间件 + 用户模型 |
| database | SQLAlchemy 配置 + 迁移脚本 |
| testing | pytest 配置 + 示例测试 |
| ci | GitHub Actions 工作流 |

### 执行步骤

1. 检查当前目录是否是一个项目（查找配置文件）
2. 如果不是，提醒用户先 `create`
3. 检测项目类型（api/web/cli/lib）
4. 生成组件文件
5. 更新依赖配置
6. 输出添加摘要
```

关键模式：**命令之间共享 Skill 级别的约束**，但各自有独立的步骤：

```markdown
## 全局约束（所有命令通用）

- 不要覆盖已存在的文件——如果文件已存在，先询问用户
- 所有生成的代码必须包含注释说明
- 使用当前目录作为项目根目录
```

## 5.3 默认命令

当用户不指定具体命令时，Skill 应该有合理的默认行为：

```markdown
## 默认行为

如果用户没有使用具体命令（如只说"帮我创建一个项目"），根据上下文判断：
- 如果当前目录为空 → 执行 `create`
- 如果当前目录已有项目 → 询问用户想要 `add` 组件还是 `config`
```

## 5.4 让 Multi-Pass 的每个 Pass 可单独执行

回到第 4 章的 `api-doc-writer`。加入命令系统后，每个 Pass 变成了可单独调用的命令：

```markdown
## Commands

| Command | Purpose |
|---------|---------|
| `/api-doc-writer write` | 完整 3-Pass 流程 |
| `/api-doc-writer discover` | 仅 Pass 1：发现端点 |
| `/api-doc-writer generate` | 仅 Pass 2：生成文档（需要先执行 discover） |
| `/api-doc-writer format` | 仅 Pass 3：格式化整合 |
```

这让用户可以：
- 只执行 `discover` 看端点清单
- 手动修改端点清单后再执行 `generate`
- 文档需要重新格式化时只执行 `format`

## 5.5 案例解剖：tech-book-writer 的 14 个命令

`tech-book-writer` 是一个拥有 14 个命令的大型 Skill。让我们分析它的命令设计：

```
plan        → 书籍规划
outline     → 大纲生成
outline <N> → 单章节大纲
draft <N>   → 起草章节
review <N>  → 审查章节
consistency → 一致性审计
glossary    → 术语表
roadmap     → 路线图
cover       → 封面生成
illustrate <N> → 章节插图
illustrate all → 全部插图
build-pdf   → PDF 构建
translate <N>  → 翻译章节
translate all  → 翻译全部
```

设计亮点：

1. **工作流顺序**：命令的排列暗示了工作流——plan → outline → draft → review

2. **带参数 vs 不带参数**：`draft <N>` 需要指定章节号，`consistency` 自动检查全部

3. **单个 vs 批量**：`illustrate <N>` 和 `illustrate all` 提供了两种粒度

4. **为什么不拆成多个 Skill？** 因为这些命令共享同一个知识域（书籍写作方法论），拆开后每个 Skill 都需要重复加载相同的背景知识。而且它们有内在的依赖关系——`draft` 需要 `outline` 的输出，`review` 需要 `draft` 的输出。

## 5.6 命令设计的反模式

### 反模式 1: 功能不相关的命令硬塞在一起

```yaml
# 坏：代码审查和项目创建不应在同一个 Skill
/dev-tools review    → 代码审查
/dev-tools create    → 创建项目
/dev-tools deploy    → 部署应用
```

这三个命令属于完全不同的知识域。合并只会让 description 变得模糊。

### 反模式 2: 命令粒度过细

```yaml
# 坏：拆得太细了
/code-review check-security
/code-review check-performance
/code-review check-readability
/code-review check-naming
/code-review check-error-handling
```

除非用户真的需要只检查某一个维度，否则应该合并为一个 `review` 命令，内部按清单检查所有维度。

### 反模式 3: 命名不一致

```yaml
# 坏：动词风格不一致
/project make        → 动词
/project addition    → 名词
/project showing     → 动名词
```

保持一致的动词风格：create, add, show 或 make, add, display——但不要混用。

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 相关功能拆成多个 Skill | 一个 Skill 多个命令 |
| Multi-Pass 只能全程执行 | 每个 Pass 可单独调用 |
| Skill 只有一种调用方式 | 命令表提供多种入口 |

**Cumulative capability**: 你的 `project-scaffold` Skill 有 4 个命令，`api-doc-writer` 有 4 个命令。你掌握了命令系统设计。

## Try It Yourself

> 完整代码见 `code/track-1/ch05-project-scaffold/`，可直接复制到 `~/.qoder/skills/` 使用。
>
> **Track 2 演进**：对比 `code/track-2/v04-multi-pass/` 和 `code/track-2/v05-commands/` 的 diff，
> 观察命令路由表（create/review/improve）如何从 89 行扩展到 134 行。

1. **Verify**: 创建 `project-scaffold` Skill，测试 `create api` 和 `add auth` 两个命令。
2. **Extend**: 给 `api-doc-writer` 加入命令路由，让 `discover`、`generate`、`format` 可以单独执行。
3. **Explore**: 分析你最常用的 CLI 工具（git, npm, docker）的命令设计。哪些设计模式适合 Skill？

## Summary

- 命令系统让一个 Skill 暴露**多个操作入口**
- 命令表用 `| Command | Purpose |` 格式放在 SKILL.md 开头
- 命令命名：`/skill-name verb [argument]`
- Multi-Pass 的每个 Pass 可以变成独立命令
- 相关功能合并成命令，不相关功能拆成不同 Skill
- 设置合理的默认行为处理无命令的调用

## Further Reading

- Git 的子命令设计：为什么 `git commit`、`git push` 在同一个工具下
- CLI 设计指南 (clig.dev)：命令行工具的交互设计最佳实践
- 第 7 章《渐进式加载》——当命令过多时如何管理 SKILL.md 的长度
