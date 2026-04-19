# Chapter 1: 你好，Agent

> **Motto**: "一个循环就是全部的开始"

> 本章你将从零开始构建一个 AI Agent。它只有不到 30 行核心代码，却能理解自然语言指令并自主调用工具完成任务。读完本章，你会拥有一个能执行 bash 命令的完整 Agent——这是整本书的种子，后续所有章节都在这个基础上生长。

![Conceptual: A simple conversation loop between human and AI](images/ch01/fig-01-01-concept.png)

*Figure 1-1. The seed of intelligence: a single loop connecting human intent to AI action.*

## 谁适合读这本书

你不需要是 AI 专家，也不需要了解机器学习或神经网络。如果你满足以下条件，就可以开始：

- 你会 Python（函数、类、字典、列表推导式）
- 你用过命令行（`cd`、`ls`、`pip install`）
- 你知道什么是 API 调用（不需要精通 HTTP）

你不需要了解：

- 机器学习或深度学习的任何知识
- Transformer 架构或注意力机制
- LangChain、AutoGen、CrewAI 等任何 Agent 框架
- 前端开发

## 你将构建什么

本书只有一个项目——**MiniAgent**。你从第一章的 30 行代码开始，到最后一章时，它将成长为一个约 2,000 行的通用智能体系统，能够：

- 理解自然语言指令，自主选择和调用工具
- 规划多步骤任务并追踪执行进度
- 管理记忆和上下文，处理任意长度的工作流
- 按需加载领域知识
- 将复杂任务分派给子智能体
- 与多个智能体协作完成团队任务
- 在安全的沙箱环境中运行，行为完全可观测

整个过程不依赖任何 Agent 框架——你亲手写每一行代码，理解每一个组件为什么存在。

## 学习路径

```
Phase 1: THE LOOP               Phase 2: PLANNING
  Ch01 → Ch02 → Ch03              Ch04 → Ch05 → Ch06
  循环    工具    记忆              规划    知识    上下文
    ↑
  你在这里

Phase 3: DELEGATION              Phase 4: COLLABORATION
  Ch07 → Ch08 → Ch09              Ch10 → Ch11 → Ch12 → Ch13
  子Agent  后台    持久化            团队    协议    自主     隔离

Phase 5: PRODUCTION
  Ch14 → Ch15 → Ch16
  安全    观测    部署
```

本书需要从头读到尾——每一章的代码都建立在前一章之上。如果你跳过了某一章，后面的代码将无法运行。

> **Tip**: 每一章都有一个对应的 git tag。如果你想快速切换到任意章节的代码状态，运行 `git checkout ch01`（或 `ch02`、`ch03`......）。

## 什么是 AI Agent？

打开 ChatGPT，输入"帮我把桌面上的图片压缩一下"，它会给你一段教程。打开一个 AI Agent，输入同样的话，它会自己找到图片、调用压缩工具、把结果放回桌面。

这就是 Agent 和聊天机器人的区别：

| 聊天机器人 | AI Agent |
|-----------|----------|
| 生成文本 | 执行操作 |
| 告诉你怎么做 | 自己去做 |
| 单轮问答 | 多步骤工作流 |
| 被动响应 | 自主决策 |

Agent 的三个核心特征：

1. **自主决策**：它决定下一步做什么，而不是你告诉它每一步
2. **工具使用**：它能调用外部工具——执行命令、读写文件、调用 API
3. **目标导向**：它朝着完成任务的方向持续行动，直到任务结束

这并不意味着 Agent 背后有什么魔法。恰恰相反——正如你马上会看到的，一个 Agent 的核心机制简单到令人惊讶。

## Agent = Model + Harness

理解 Agent 有一个关键的思维模型：

```
Agent = Model + Harness
```

**Model**（模型）提供智能——它理解自然语言，知道何时该调用什么工具，能够做出合理的决策。这部分由 Claude、GPT-4 等大语言模型提供，你不需要自己训练。

**Harness**（调度框架）提供能力——它连接了工具、知识、权限和行动接口，是模型和真实世界之间的桥梁。

```
┌─────────────────────────────────┐
│            Harness              │
│  ┌─────────┐  ┌──────────────┐ │
│  │  Model   │  │    Tools     │ │
│  │ (Claude) │  │ bash, files  │ │
│  └────┬─────┘  └──────┬───────┘ │
│       │    Agent Loop  │         │
│       └───────┬────────┘         │
│               ↓                  │
│         Real World               │
└─────────────────────────────────┘
```

模型就像一个聪明的大脑，Harness 就像它的手脚和感官。本书要做的，就是构建这个 Harness。

用一个公式来描述 Harness 包含什么：

```
Harness = Tools + Knowledge + Observation + Action Interfaces + Permissions
```

- **Tools**（工具）：Agent 能调用的能力，如执行命令、读写文件
- **Knowledge**（知识）：领域知识和参考资料
- **Observation**（观察）：Agent 感知环境的方式
- **Action Interfaces**（行动接口）：Agent 与外部系统交互的方式
- **Permissions**（权限）：Agent 被允许做什么

你不需要一次理解所有这些。本章只涉及最基本的——一个工具（bash），加上最简单的循环。

## 环境搭建

### 安装 Python

确保你的 Python 版本 >= 3.10：

```bash
python3 --version
# Python 3.10.x 或更高
```

### 创建项目

```bash
mkdir miniagent && cd miniagent
python3 -m venv .venv
source .venv/bin/activate  # Windows 用户: .venv\Scripts\activate
```

### 安装依赖

本书使用 Anthropic 的 Claude API。安装 SDK：

```bash
pip install anthropic
```

> **Note**: 本书的代码同样适用于 OpenAI 的 API，只需修改少量调用代码。附录 A 提供了两种 API 的对照。我们选择 Anthropic 是因为它的工具调用 API 设计更清晰。

### 配置 API Key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

> **Warning**: 永远不要把 API Key 写在代码里或提交到 git。使用环境变量或 `.env` 文件。

### 验证环境

创建 `verify_setup.py` 并运行：

```python
# verify_setup.py
import sys
import os

print(f"Python: {sys.version}")

try:
    import anthropic
    print(f"anthropic: {anthropic.__version__} ✓")
except ImportError:
    print("anthropic: 未安装 ✗  →  pip install anthropic")

key = os.environ.get("ANTHROPIC_API_KEY", "")
print(f"API Key: {'已设置 ✓' if key else '未设置 ✗'}")
```

```bash
python verify_setup.py
```

预期输出：

```
Python: 3.12.x
anthropic: 0.39.x ✓
API Key: 已设置 ✓
```

如果三项都通过，你已经准备好了。

## 第一个 Agent 循环

现在来写最重要的代码——Agent 的核心循环。

创建 `agent.py`，从导入和配置开始：

```python
import os
import sys
import subprocess
import anthropic

MODEL = "claude-sonnet-4-20250514"
SYSTEM = "你是一个有用的 AI 助手。你可以通过工具与计算机交互来完成任务。"
```

`MODEL` 指定使用的 LLM 模型。`SYSTEM` 是系统提示词，告诉模型它是谁、能做什么。

### 定义工具

Agent 需要知道自己有哪些工具可用。工具通过 JSON Schema 描述：

```python
TOOLS = [
    {
        "name": "bash",
        "description": "在系统 shell 中执行命令。用于运行程序、查看文件列表、安装依赖等操作。",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的 bash 命令",
                }
            },
            "required": ["command"],
        },
    }
]
```

这个 schema 告诉模型：你有一个叫 `bash` 的工具，它接受一个 `command` 参数，可以用来执行 shell 命令。模型并不会直接执行命令——它只是告诉你"我想调用 bash，参数是 `ls -la`"，然后由你的代码来实际执行。

> **Important**: 工具的 `description` 字段极其重要。模型完全依赖这段文字来决定何时使用这个工具。一个含糊的描述会导致模型误用或不用。

### 实现工具处理函数

```python
def handle_bash(command: str) -> str:
    """执行 bash 命令并返回输出。"""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout
        if result.returncode != 0:
            output += f"\n[stderr]\n{result.stderr}" if result.stderr else ""
            output += f"\n[exit code: {result.returncode}]"
        return output if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return "[error: command timed out after 30s]"
```

这段代码做了三件事：

1. 用 `subprocess.run` 执行命令
2. 捕获 stdout 和 stderr
3. 设置 30 秒超时防止命令卡住

注意返回值永远是字符串——工具的输出会被送回 LLM，而 LLM 只理解文本。

### 核心循环

这是整个 Agent 的心脏——一个 while 循环：

```python
def agent_loop(messages: list) -> None:
    """Agent 的核心：一个 while 循环。"""
    client = anthropic.Anthropic()

    while True:
        # 1. 发送消息给 LLM
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
        )

        # 2. 把 LLM 的回复追加到消息列表
        messages.append({"role": "assistant", "content": response.content})

        # 3. 如果 LLM 没有请求工具调用，结束循环
        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nAgent: {block.text}")
            return

        # 4. 执行 LLM 请求的工具
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [Tool: {block.name}] {block.input.get('command', '')}")
                output = handle_bash(**block.input)
                print(f"  {output[:200]}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })

        # 5. 把工具结果送回 LLM，继续循环
        messages.append({"role": "user", "content": tool_results})
```

让我们逐步拆解这个循环。它看起来只有 30 行，但每一行都值得理解。

**第 1 步：发送消息给 LLM**

```python
response = client.messages.create(
    model=MODEL,
    max_tokens=4096,
    system=SYSTEM,
    messages=messages,
    tools=TOOLS,
)
```

你把当前的消息列表（包含用户的请求和所有历史交互）发送给 LLM。同时传递了可用的工具列表——模型需要知道它能用什么。

**第 2 步：保存回复**

```python
messages.append({"role": "assistant", "content": response.content})
```

LLM 的回复被追加到消息列表。这很重要——下次调用时，LLM 会看到自己之前的回复，知道自己做过什么。

**第 3 步：检查是否需要调用工具**

```python
if response.stop_reason != "tool_use":
    return
```

LLM 有两种停止方式：

- `"end_turn"`：模型认为任务完成了，输出了文本回复
- `"tool_use"`：模型想调用一个工具

如果是 `"end_turn"`，循环结束。如果是 `"tool_use"`，继续往下。

**第 4 步：执行工具**

```python
for block in response.content:
    if block.type == "tool_use":
        output = handle_bash(**block.input)
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": output,
        })
```

遍历 LLM 回复中的每个内容块，找到工具调用请求，执行对应的处理函数，收集结果。`tool_use_id` 用于将结果与请求对应起来。

**第 5 步：送回结果，继续循环**

```python
messages.append({"role": "user", "content": tool_results})
```

工具结果以 `"user"` 角色追加到消息列表（这是 API 的约定），然后回到循环开头，LLM 看到工具结果后决定下一步——可能再调一个工具，也可能认为任务完成了。

> **Note**: 这就是 Agent 的全部秘密。不是什么深度学习魔法，不是什么复杂的状态机——就是一个 while 循环。模型决定做什么，你执行，把结果送回去，模型再决定，你再执行......直到模型说"完成了"。

### 添加入口

```python
def main():
    if len(sys.argv) < 2:
        print("用法: python agent.py <你的指令>")
        sys.exit(1)

    user_input = " ".join(sys.argv[1:])
    messages = [{"role": "user", "content": user_input}]

    print(f"You: {user_input}")
    agent_loop(messages)

if __name__ == "__main__":
    main()
```

## 运行你的第一个 Agent

保存文件，运行：

```bash
python agent.py "列出当前目录的文件，并告诉我一共有多少个"
```

你应该看到类似这样的输出：

```
You: 列出当前目录的文件，并告诉我一共有多少个
  [Tool: bash] ls -la
  total 16
  -rw-r--r--  1 user  staff  2048 Apr 17 10:00 agent.py
  -rw-r--r--  1 user  staff    42 Apr 17 10:00 requirements.txt
  -rw-r--r--  1 user  staff   512 Apr 17 10:00 verify_setup.py

Agent: 当前目录有 3 个文件：agent.py、requirements.txt 和 verify_setup.py。
```

看看发生了什么：

1. 你说"列出文件并告诉我有多少"
2. LLM 分析你的请求，决定需要用 `bash` 工具
3. LLM 输出"我要调用 bash，参数是 `ls -la`"
4. 你的代码执行了 `ls -la`，把输出送回 LLM
5. LLM 看到文件列表，数了一下，回答"3 个文件"

整个过程中，你没有写任何"如果用户问文件数量就执行 ls"的逻辑。模型自己决定了需要什么工具、什么参数。这就是 Agent 的核心价值。

试试更复杂的任务：

```bash
python agent.py "创建一个名为 hello.py 的 Python 文件，内容是打印 Hello World，然后运行它"
```

观察 Agent 如何自主完成多个步骤——创建文件、写入内容、执行文件——全程无需你的干预。

## What Changed

这是第一章，没有"之前"可以比较。但让我们记录当前的起点：

| 状态 | 描述 |
|------|------|
| 核心文件 | `agent.py` (~90 lines) |
| 工具数量 | 1 (bash) |
| Agent 能做什么 | 执行单条或多条 bash 命令 |
| Agent 不能做什么 | 读写文件（要通过 bash）、记住对话、规划任务 |

**你的 MiniAgent 目前的架构**：

```
┌──────────────────┐
│   agent_loop()   │
│  ┌────────────┐  │
│  │   LLM      │  │
│  └─────┬──────┘  │
│        ↓         │
│  ┌────────────┐  │
│  │   bash     │  │
│  └────────────┘  │
└──────────────────┘
```

在后续章节中，这张图会不断扩展。到第 13 章时，这里会有 22 个工具、子智能体、团队协作、工作隔离——但核心循环始终不变。

## Try It Yourself

1. **Verify**: 运行 `python agent.py "当前的操作系统是什么？"`，确认 Agent 能调用 bash 工具并返回结果。

2. **Extend**: 修改 `handle_bash` 函数，在每次执行命令前打印一行 `>>> Executing: <command>`。这能帮你更清楚地观察 Agent 的行为。

3. **Explore**: 给 Agent 一个需要多步工具调用的任务，例如"创建一个目录叫 test_dir，在里面创建 3 个文件，然后列出目录内容"。观察 Agent 循环执行了多少轮。思考一下：是什么让 LLM 知道任务还没完成？

## Summary

- **AI Agent** 的核心是一个循环：LLM 思考 → 调用工具 → 返回结果 → LLM 再思考
- **Agent = Model + Harness**：模型提供智能，Harness 提供能力。本书构建的是 Harness
- Agent 的核心循环不到 30 行代码，但它是整个系统的基础
- 工具通过 JSON Schema 描述，模型根据描述决定何时使用什么工具
- `stop_reason` 是循环的开关：`"tool_use"` 继续，`"end_turn"` 结束

下一章，你将给 Agent 更多的工具——让它不再需要通过 bash 绕路来读写文件。

## Further Reading

- [Anthropic Tool Use Documentation](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview) — 工具调用的官方文档
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) — Agent 工具的标准化协议
- Yao, S., et al. (2023). "ReAct: Synergizing Reasoning and Acting in Language Models." *ICLR 2023* — Agent 推理-行动循环的理论基础
