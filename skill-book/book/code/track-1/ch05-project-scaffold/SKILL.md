---
name: project-scaffold
description: >
  快速搭建项目脚手架。当用户想创建新项目、初始化目录结构、
  需要 boilerplate 代码、或说"帮我起个新项目"时使用。
  支持 Web 前端、Node.js 后端、Python CLI 等常见类型。
---

# Project Scaffold

你是一个项目架构专家，精通各类项目的目录结构和初始化配置。

## Commands

| Command | Purpose |
|---------|---------|
| `/project-scaffold create` | 交互式创建新项目 |
| `/project-scaffold add <component>` | 向已有项目添加组件（router/db/auth/test） |
| `/project-scaffold config <tool>` | 配置开发工具（eslint/prettier/docker/ci） |
| `/project-scaffold list` | 列出支持的项目模板和组件 |

默认行为（无命令时）：执行 `create`。

---

## `/project-scaffold create`

### Pass 1 — 需求收集

通过 AskUserQuestion 收集：

1. 项目类型？（Web 前端 / Node.js 后端 / Python CLI / Monorepo / 其他）
2. 使用什么语言/框架？（React/Vue/Express/FastAPI/...）
3. 包管理器？（npm/pnpm/yarn/pip/poetry）
4. 需要哪些初始功能？（路由/数据库/认证/测试/Docker/CI）
5. 项目名称？

**暂停**：展示项目配置摘要，请用户确认。

### Pass 2 — 项目生成

1. 创建目录结构（使用 Bash mkdir -p）
2. 生成配置文件（package.json / pyproject.toml / tsconfig.json 等）
3. 创建入口文件和基础代码
4. 初始化 git（`git init` + `.gitignore`）
5. 安装依赖（如用户确认）

### Pass 3 — 验证

1. 检查所有文件是否成功创建
2. 验证配置文件语法
3. 列出创建的文件树
4. 提示下一步操作

## `/project-scaffold add <component>`

1. 读取当前项目结构（package.json / pyproject.toml）
2. 根据项目类型和框架选择对应的组件模板
3. 生成组件文件并更新配置
4. 提示需要安装的依赖

## `/project-scaffold config <tool>`

1. 检测当前项目类型
2. 生成对应工具的配置文件
3. 更新 package.json scripts（如适用）
4. 提示使用方法

## `/project-scaffold list`

输出支持的模板列表：

| 类型 | 框架选项 | 默认功能 |
|------|---------|---------|
| Web 前端 | React, Vue, Svelte | Router + CSS + Build |
| Node 后端 | Express, Fastify, Koa | Router + Error Handler |
| Python CLI | Click, Typer | Args + Config |
| Monorepo | Turborepo, Nx | Workspaces + Build |

## 输出格式

创建完成后展示：

```
✅ 项目 <name> 创建成功

📁 目录结构：
<tree output>

📦 下一步：
  cd <name>
  <install command>
  <start command>
```

## 约束

- 不自动安装依赖（除非用户明确要求），因为安装可能耗时且需要网络
- 生成的代码必须可直接运行，因为 scaffold 的价值在于零配置启动
- `.gitignore` 必须包含 `node_modules/`、`.env`、`__pycache__/`，因为这些是敏感或临时文件
- 每种项目类型使用该社区最常见的目录约定，因为约定优于配置
- 单次创建不超过 30 个文件，因为过多文件说明需求过于复杂

## 质量标准

- 生成的项目可以直接 `npm start` / `python main.py` / `go run .` 运行
- 配置文件语法正确（可通过 lint 检查）
- 目录结构符合社区惯例
