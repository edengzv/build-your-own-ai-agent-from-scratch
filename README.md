# 智能体入门：从零构建通用 AI Agent

> Build Your Own AI Agent from Scratch

本书采用"从零构建"的方法论，带领读者从一个不到 30 行代码的 Agent 循环开始，逐章添加一个新能力，最终构建出一个功能完备的通用智能体系统 —— **MiniAgent**。

## 快速开始

```bash
# 克隆项目
git clone <repo-url>
cd hermas

# 切换到任意章节的代码状态
git checkout ch01    # Chapter 1: 你好，Agent
git checkout ch02    # Chapter 2: 工具调用
git checkout ch03    # Chapter 3: 对话记忆
# ... 以此类推

# 安装依赖
pip install -r miniagent/requirements.txt

# 运行
python miniagent/agent.py "你好，帮我列出当前目录的文件"
```

## 项目结构

```
hermas/
├── book/                   # 书籍内容 (Markdown)
│   ├── book-meta.md        # 书籍元信息
│   ├── outline.md          # 完整大纲
│   ├── roadmap.md          # 学习路径图
│   ├── chapters/           # 各章节内容
│   └── code/               # 各章节代码快照 (参考)
├── miniagent/              # MiniAgent 主项目 (累积演进的代码)
│   ├── agent.py            # 核心 Agent
│   ├── requirements.txt    # 依赖
│   └── ...                 # 各章节逐步添加的模块
└── README.md
```

## 章节标签

每个 git tag 对应一个章节完成时的代码状态：

| Tag | Chapter | 系统状态 |
|-----|---------|---------|
| `ch01` | 你好，Agent | 1 tool, 基础循环 |
| `ch02` | 工具调用 | 4 tools, 工具分发 |
| `ch03` | 对话记忆 | 4 tools, 多轮对话 REPL |
| `ch04` | 任务规划 | 5 tools, TodoManager |
| `ch05` | 知识加载 | 6 tools, Skill 系统 |
| `ch06` | 上下文管理 | 7 tools, 上下文压缩 |
| `ch07` | 子智能体 | 7 tools (+task), Subagent |
| `ch08` | 后台任务 | 8 tools, 异步执行 |
| `ch09` | 持久化任务 | 11 tools, 任务 DAG |
| `ch10` | 智能体团队 | 14 tools, 邮箱通信 |
| `ch11` | 团队协议 | 18 tools, 请求-响应 |
| `ch12` | 自主智能体 | 20 tools, IDLE/WORK |
| `ch13` | 工作隔离 | 22 tools, Worktree |
| `ch14` | 安全与权限 | 22 tools (+sandbox) |
| `ch15` | 可观测性 | 22 tools (+logging) |
| `ch16` | 从 MiniAgent 到生产 | 回顾与展望 |

## 前置要求

- Python 3.10+
- 一个 LLM API Key (支持 Anthropic Claude 或 OpenAI GPT-4)
- macOS / Linux / WSL

## License

MIT
