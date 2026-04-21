# The Art of Skill Engineering

**Skill 工程：写给 AI 时代的技能设计指南**

*A Practical Guide to Crafting AI Agent Skills*

<p align="center">
  <img src="book/images/cover-oreilly.png" alt="Book Cover" width="360" />
</p>

---

> **[PDF 下载](https://github.com/edengzv/The-Art-of-Skill-Engineering/releases/latest/download/book-zh.pdf)** | **[HTML 在线阅读](https://github.com/edengzv/The-Art-of-Skill-Engineering/releases/latest/download/book-zh.html)** | **[所有版本](https://github.com/edengzv/The-Art-of-Skill-Engineering/releases)**

---

AI Agent 正在改变软件开发的方式。Claude Code、Cursor、Qoder 等工具让 Agent 能读写文件、执行命令、搜索代码。但大多数人只是在对话中反复描述同样的需求——每次都要重新说一遍，Agent 每次都从零开始理解。

**Skill** 是解决这个问题的答案。一个 Skill 就是一份结构化的指令文件（SKILL.md），告诉 Agent「当你需要做 X 的时候，按照这些步骤来」。写好一个 Skill，等于训练了一个永不遗忘的专家助手。

本书从第一个 10 行 Skill 开始，逐步教你掌握 description 的精确表达、指令的可执行性、多步工作流设计、模板锚定、质量自检、多工具编排等核心技巧。每一章你都会写出一个真实可用的 Skill，到最后你将拥有一整套自己的 Skill 工具箱。

## 目录

### Phase 1: FIRST SKILL — 写出你的第一个 Skill

| # | 章节 | Motto | 核心技巧 |
|---|------|-------|----------|
| 1 | [你好，Skill](book/chapters/ch01-hello-skill.md) | 一个 SKILL.md 文件就是全部的开始 | 理解 Skill 结构 + 写出第一个 10 行 Skill |
| 2 | [Description：最重要的一行](book/chapters/ch02-description.md) | Agent 看不到你的 Skill 内容，只看到 description | 精准的 description 写作 |
| 3 | [可执行的指令](book/chapters/ch03-executable-instructions.md) | 模糊的指令产生模糊的结果 | 从模糊到精确的指令写作 |

### Phase 2: CORE CRAFT — 核心写作技巧

| # | 章节 | Motto | 核心技巧 |
|---|------|-------|----------|
| 4 | [工作流设计模式](book/chapters/ch04-multi-pass.md) | 把大象装进冰箱需要三步，好的 Skill 也是 | Multi-Pass 工作流设计 |
| 5 | [命令与路由](book/chapters/ch05-commands-routing.md) | 一个 Skill 多种用法，由命令来切换 | 命令表 + 子命令路由 |
| 6 | [模板与示例](book/chapters/ch06-templates-examples.md) | 一个好的示例胜过十段解释 | 示例锚定 + 输出模板 |

### Phase 3: ARCHITECTURE — 高级架构模式

| # | 章节 | Motto | 核心技巧 |
|---|------|-------|----------|
| 7 | [渐进式加载](book/chapters/ch07-progressive-loading.md) | 上下文是公共资源，每个 Token 都很宝贵 | SKILL.md + scripts/ + reference/ 三层架构 |
| 8 | [多工具编排](book/chapters/ch08-multi-tool-orchestration.md) | Skill 的力量不在文字，在于它能调动的工具 | 工具声明 + 编排模式 |
| 9 | [质量检查清单](book/chapters/ch09-quality-checklist.md) | 好的 Skill 自己知道自己做得好不好 | 内置 Quality Checklist |

### Phase 4: MASTERY — 从技巧到精通

| # | 章节 | Motto | 核心技巧 |
|---|------|-------|----------|
| 10 | [测试与调优](book/chapters/ch10-testing-tuning.md) | 写完不是终点，验证才是 | Skill 评估方法论 + A/B 迭代 |
| 11 | [案例解剖室](book/chapters/ch11-case-studies.md) | 最好的学习方式是拆解大师的作品 | 解剖真实优秀 Skill |
| 12 | [元技能：创建 Skill 的 Skill](book/chapters/ch12-meta-skill.md) | 教会 Agent 创建 Skill，你就不再是一个人在写 | Meta-Skill 设计模式 |

### 附录

| 附录 | 内容 |
|------|------|
| [附录 A](book/appendices/appendix-a-anti-patterns.md) | 十大反模式 |
| [附录 B](book/appendices/appendix-b-pre-launch-checklist.md) | 上线前检查清单 |
| [附录 C](book/appendices/appendix-c-ecosystem-map.md) | 全球 Skill 生态资源地图 |
| [术语表](book/glossary.md) | 关键术语定义 |
| [参考文献](book/bibliography.md) | 引用资源 |

## 读者的 Skill 工具箱

跟随本书，你将构建一个不断演进的 Skill 工具箱：

```
10 行  ████                                          Ch01  quick-fix
30 行  ████████                                      Ch02  code-review
50 行  ████████████                                  Ch03  commit-message
100 行 ████████████████████████                      Ch04  api-doc-writer
120 行 ████████████████████████████                  Ch05  project-scaffold
150 行 ████████████████████████████████████          Ch06  test-writer
200 行 ████████████████████████████████████████████  Ch07  refactor-guide
250 行 ████████████████████████████████████████████████████  Ch08  deploy-checker
200 行 ████████████████████████████████████████████  Ch09  pr-reviewer
320 行 ████████████████████████████████████████████████████████████████  Ch12  skill-creator
```

## 代码示例

本书采用**双轨并行**的代码架构：

- **[Track 1](book/code/track-1/)** — 每章独立 Skill，完整、可直接使用
- **[Track 2](book/code/track-2/)** — `skill-creator` 从 v01 到 v12 的渐进演进，展示技巧的累积效果

详见 [代码说明](book/code/README.md)。

```bash
# 快速使用：复制任意 Skill 到你的 skills 目录
cp -r book/code/track-1/ch09-pr-reviewer/ ~/.qoder/skills/pr-reviewer/

# 对比相邻版本，理解每项技巧如何改进 Skill
diff book/code/track-2/v06-examples/SKILL.md book/code/track-2/v07-architecture/SKILL.md
```

## 适合谁读

**你应该读这本书，如果你：**
- 使用 Claude Code / Cursor / Qoder 等 AI 编程工具，想让 Agent 记住你的工作流程
- 写过 Prompt 但没写过 Skill，想系统学习
- 是技术团队 Lead，想通过 Skill 将团队最佳实践标准化

**你不需要提前知道：**
- 机器学习或深度学习
- Agent 框架的内部实现
- 编程语言（但会编程的读者会获得更多）

**你需要准备：**
- Claude Code / Cursor / Qoder 中的任意一个
- 基本的命令行操作能力
- 好奇心

## 本书特色

| 维度 | 本书 | 其他资源 |
|------|------|----------|
| 方法论 | 渐进式，从 10 行到 300+ 行 | 官方文档只给格式规范 |
| 案例 | 20+ 真实 Skill 完整解剖 | 大多只给模板 |
| 深度 | 教 WHY（为什么这样写有效） | 社区教程停留在 HOW |
| 体系 | 从 description 到分发的完整流程 | 零散的技巧文章 |
| 实践 | 每章一个你能立刻用上的 Skill | 理论多于实操 |

## 项目结构

```
skill-book/
├── README.md                 # 本文件
├── book/
│   ├── book-meta.md          # 书籍元信息
│   ├── outline.md            # 完整大纲
│   ├── roadmap.md            # 写作路线图
│   ├── chapters/             # 12 章正文
│   │   ├── ch01-hello-skill.md
│   │   ├── ch02-description.md
│   │   ├── ...
│   │   └── ch12-meta-skill.md
│   ├── code/                 # 双轨代码示例
│   │   ├── track-1/          # 每章独立 Skill
│   │   └── track-2/          # skill-creator 渐进演进
│   ├── appendices/           # 附录 + 研究资料
│   ├── images/               # 封面 + 章节配图
│   ├── glossary.md           # 术语表
│   └── bibliography.md       # 参考文献
└── .gitignore
```

## License

All rights reserved. This content is provided for personal learning and reference.

---

> *"写好一个 Skill，等于训练了一个永不遗忘的专家助手。"*
