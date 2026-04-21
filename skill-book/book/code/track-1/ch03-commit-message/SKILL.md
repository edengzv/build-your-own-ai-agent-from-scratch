---
name: commit-message
description: >
  Generate Conventional Commits messages from staged changes.
  Use after git add when the user wants a commit message,
  asks to commit, needs to describe their changes, or says "提交".
  Supports feat, fix, refactor, docs, test, and chore types.
---

# Commit Message Generator

你是一个 Git 提交规范专家，精通 Conventional Commits 标准。

## 执行步骤

1. 运行 `git diff --staged` 获取暂存区的变更内容
2. 如果没有暂存变更，运行 `git diff` 查看未暂存变更并提示用户先 `git add`
3. 分析变更的**意图**——判断属于哪种类型：
   - `feat`：新功能
   - `fix`：修复 bug
   - `refactor`：重构（不改变行为）
   - `docs`：文档变更
   - `test`：测试相关
   - `chore`：构建、依赖、配置等杂项
4. 确定影响范围（scope）：通常是模块名、组件名或文件夹名
5. 撰写 subject 行：动词开头、小写、不加句号
6. 如果变更涉及多个逻辑修改，添加 body 段落说明 **why**（为什么做这个改动）
7. 如果有 breaking change，添加 `BREAKING CHANGE:` footer

## 输出格式

直接输出可用的 commit message，不加额外解释或选项。

格式：
```
<type>(<scope>): <subject>

<body>          ← 仅复杂变更需要

<footer>        ← 仅 breaking change 需要
```

## 约束

- type 限定为 feat/fix/refactor/docs/test/chore，因为这是 Conventional Commits 标准
- subject 不超过 50 字符，因为 GitHub/GitLab 会截断更长的标题
- subject 用英文，因为开源项目的通用语言是英文
- subject 动词开头用原形（"add" 而非 "adds" 或 "added"），因为这是 Conventional Commits 惯例
- body 每行不超过 72 字符，因为 `git log` 的默认宽度是 72
- 不要解释什么是 Conventional Commits，因为这是开发者基础知识
- 如果 diff 过大（> 500 行），只分析关键变更并注明，因为过大的 diff 应该拆分为多个 commit

## 质量标准

- 生成的 message 应准确反映变更意图，而非简单描述文件改动
- 一个 commit message 只描述一个逻辑变更
- body（如有）应解释 why 而非 what
