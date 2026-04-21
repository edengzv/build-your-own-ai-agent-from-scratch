# 智能体入门：从零构建通用 AI Agent

> Build Your Own AI Agent from Scratch

本书采用"从零构建"的方法论，带领读者从一个不到 30 行代码的 Agent 循环开始，逐章添加一个新能力，最终构建出一个功能完备的通用智能体系统 —— **MiniAgent**。

## 下载阅读

| 版本 | PDF | HTML (含图片) |
|------|-----|------|
| 中文版 (214 页) | [book-zh.pdf](https://github.com/edengzv/build-your-own-ai-agent-from-scratch/releases/download/v1.0.0/book-zh.pdf) | [book-zh-html.zip](https://github.com/edengzv/build-your-own-ai-agent-from-scratch/releases/download/v1.0.0/book-zh-html.zip) |
| English (224 pages) | [book-en.pdf](https://github.com/edengzv/build-your-own-ai-agent-from-scratch/releases/download/v1.0.0/book-en.pdf) | [book-en-html.zip](https://github.com/edengzv/build-your-own-ai-agent-from-scratch/releases/download/v1.0.0/book-en-html.zip) |

> PDF 采用 O'Reilly 风格排版 (7x9.25")。HTML 版本带侧边栏目录导航，下载 zip 解压后在浏览器中打开即可阅读。

## 快速开始

```bash
# 克隆项目
git clone https://github.com/edengzv/build-your-own-ai-agent-from-scratch.git
cd build-your-own-ai-agent-from-scratch

# 安装依赖
pip install -r miniagent/requirements.txt

# 运行最终版本（miniagent/ 目录始终保持最新状态）
python miniagent/agent.py "你好，帮我列出当前目录的文件"
```

## 阅读某个章节的代码

每个章节都有独立的代码快照，位于 `book/code/chXX/` 目录中。推荐直接使用这些快照：

```bash
# 方式一（推荐）：直接运行章节代码快照
cd book/code/ch01
python agent.py "你好，帮我列出当前目录的文件"

# 方式二：使用 git tag 切换到章节状态（ch01-ch09 可用）
git checkout ch01
python miniagent/agent.py "你好，帮我列出当前目录的文件"
```

> **注意**: `book/code/chXX/` 目录中的代码快照是最权威的参考。git tag `ch01`-`ch09` 与快照完全一致；`ch10`-`ch16` 的 tag 存在部分模块为空占位符的历史问题，请使用 `book/code/` 目录中的快照。

## 项目结构

```
hermas/
├── book/                   # 书籍内容 (Markdown)
│   ├── book-meta.md        # 书籍元信息
│   ├── outline.md          # 完整大纲
│   ├── roadmap.md          # 学习路径图
│   ├── chapters/           # 各章节内容
│   └── code/               # 各章节代码快照（权威参考）
│       ├── ch01/           # Chapter 1 的完整可运行代码
│       ├── ch02/           # Chapter 2 的完整可运行代码
│       └── ...             # 每章一个独立目录
├── miniagent/              # MiniAgent 最终版（= ch16 完整代码）
│   ├── agent.py            # 核心 Agent
│   ├── requirements.txt    # 依赖
│   └── ...                 # 全部模块
└── README.md
```

## 章节标签

每个章节对应 `book/code/chXX/` 中的独立代码快照，同时也有 git tag 可切换：

| 章节 | 代码快照 | 系统状态 |
|------|---------|---------|
| Ch01: 你好，Agent | `book/code/ch01/` | 1 tool, 基础循环 |
| Ch02: 工具调用 | `book/code/ch02/` | 4 tools, 工具分发 |
| Ch03: 对话记忆 | `book/code/ch03/` | 4 tools, 多轮对话 REPL |
| Ch04: 任务规划 | `book/code/ch04/` | 5 tools, TodoManager |
| Ch05: 知识加载 | `book/code/ch05/` | 6 tools, Skill 系统 |
| Ch06: 上下文管理 | `book/code/ch06/` | 7 tools, 上下文压缩 |
| Ch07: 子智能体 | `book/code/ch07/` | 8 tools, Subagent |
| Ch08: 后台任务 | `book/code/ch08/` | 10 tools, 异步执行 |
| Ch09: 持久化任务 | `book/code/ch09/` | 14 tools, 任务 DAG |
| Ch10: 智能体团队 | `book/code/ch10/` | 18 tools, 邮箱通信 |
| Ch11: 团队协议 | `book/code/ch11/` | 23 tools, 请求-响应 |
| Ch12: 自主智能体 | `book/code/ch12/` | 26 tools, IDLE/WORK |
| Ch13: 工作隔离 | `book/code/ch13/` | 29 tools, Worktree |
| Ch14: 安全与权限 | `book/code/ch14/` | 29 tools (+sandbox) |
| Ch15: 可观测性 | `book/code/ch15/` | 29 tools (+logging) |
| Ch16: 从 MiniAgent 到生产 | `book/code/ch16/` | 回顾与展望 |

## 前置要求

- Python 3.10+
- 一个 LLM API Key (支持 Anthropic Claude 或 OpenAI GPT-4)
- macOS / Linux / WSL

## License

MIT
