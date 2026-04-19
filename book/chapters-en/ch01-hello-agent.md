<!-- Translated from: ch01-hello-agent.md -->

# Chapter 1: Hello, Agent

> **Motto**: "A single loop is where it all begins."

> In this chapter, you build an AI agent from scratch. It has fewer than 30 lines of core code, yet it can understand natural language instructions and autonomously call tools to complete tasks. By the end, you will have a fully working agent that can execute bash commands — the seed from which every subsequent chapter grows.

![Conceptual: A simple conversation loop between human and AI](images/ch01/fig-01-01-concept.png)

*Figure 1-1. The seed of intelligence: a single loop connecting human intent to AI action.*

## Who This Book Is For

You do not need to be an AI expert, nor do you need to understand machine learning or neural networks. If you meet these conditions, you are ready to begin:

- You know Python (functions, classes, dictionaries, list comprehensions)
- You have used the command line (`cd`, `ls`, `pip install`)
- You know what an API call is (no need to master HTTP)

You do NOT need to know:

- Anything about machine learning or deep learning
- The Transformer architecture or attention mechanisms
- LangChain, AutoGen, CrewAI, or any other agent framework
- Front-end development

## What You Will Build

This book has a single project — **MiniAgent**. Starting from 30 lines of code in this first chapter, it will grow into a ~2,000-line general-purpose agent system capable of:

- Understanding natural language instructions and autonomously selecting and calling tools
- Planning multi-step tasks and tracking execution progress
- Managing memory and context to handle arbitrarily long workflows
- Loading domain knowledge on demand
- Delegating complex tasks to sub-agents
- Collaborating with multiple agents as a team
- Running in a secure sandbox with fully observable behavior

The entire process depends on no agent framework — you write every line of code by hand and understand why every component exists.

## The Roadmap

```
Phase 1: THE LOOP               Phase 2: PLANNING
  Ch01 → Ch02 → Ch03              Ch04 → Ch05 → Ch06
  loop    tools   memory           planning  skills  context
    ↑
  You are here

Phase 3: DELEGATION              Phase 4: COLLABORATION
  Ch07 → Ch08 → Ch09              Ch10 → Ch11 → Ch12 → Ch13
  sub-agent  bg tasks  persistent   team   protocols  autonomous  isolation

Phase 5: PRODUCTION
  Ch14 → Ch15 → Ch16
  security  observability  deployment
```

This book must be read front to back — every chapter's code builds on the previous one. If you skip a chapter, later code will not run.

> **Tip**: Each chapter has a corresponding git tag. To jump to any chapter's code state, run `git checkout ch01` (or `ch02`, `ch03`, etc.).

## What Is an AI Agent?

Open ChatGPT and type "compress the images on my desktop." It gives you a tutorial. Open an AI agent, type the same thing, and it finds the images itself, calls a compression tool, and puts the results back on your desktop.

That is the difference between an agent and a chatbot:

| Chatbot | AI Agent |
|---------|----------|
| Generates text | Executes actions |
| Tells you how to do it | Does it itself |
| Single-turn Q&A | Multi-step workflows |
| Passive response | Autonomous decision-making |

Three core characteristics of an agent:

1. **Autonomous decision-making**: It decides what to do next, rather than you telling it every step
2. **Tool use**: It can call external tools — execute commands, read and write files, call APIs
3. **Goal-oriented**: It keeps acting toward completing the task until it is done

This does not mean there is magic behind an agent. Quite the opposite — as you are about to see, the core mechanism of an agent is stunningly simple.

## Agent = Model + Harness

Understanding an agent requires one key mental model:

```
Agent = Model + Harness
```

**Model** provides intelligence — it understands natural language, knows when to call which tool, and can make reasonable decisions. This is provided by large language models like Claude or GPT-4; you do not need to train one yourself.

**Harness** provides capability — it connects tools, knowledge, permissions, and action interfaces, serving as the bridge between the model and the real world.

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

The model is like a brilliant brain; the harness is its hands, feet, and senses. What this book builds is the harness.

Expressed as a formula:

```
Harness = Tools + Knowledge + Observation + Action Interfaces + Permissions
```

- **Tools**: Capabilities the agent can invoke, such as executing commands or reading/writing files
- **Knowledge**: Domain knowledge and reference materials
- **Observation**: How the agent perceives its environment
- **Action Interfaces**: How the agent interacts with external systems
- **Permissions**: What the agent is allowed to do

You do not need to understand all of these at once. This chapter covers only the basics — one tool (bash) plus the simplest possible loop.

## Setting Up Your Environment

### Install Python

Make sure your Python version is >= 3.10:

```bash
python3 --version
# Python 3.10.x or higher
```

### Create the Project

```bash
mkdir miniagent && cd miniagent
python3 -m venv .venv
source .venv/bin/activate  # Windows users: .venv\Scripts\activate
```

### Install Dependencies

This book uses Anthropic's Claude API. Install the SDK:

```bash
pip install anthropic
```

> **Note**: The code in this book works equally well with OpenAI's API — only a few lines of calling code need to change. Appendix A provides a side-by-side comparison. We chose Anthropic because its tool-calling API design is cleaner.

### Configure Your API Key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

> **Warning**: Never hardcode API keys in source code or commit them to git. Use environment variables or a `.env` file.

### Verify Your Setup

Create `verify_setup.py` and run it:

```python
# verify_setup.py
import sys
import os

print(f"Python: {sys.version}")

try:
    import anthropic
    print(f"anthropic: {anthropic.__version__} ✓")
except ImportError:
    print("anthropic: not installed ✗  →  pip install anthropic")

key = os.environ.get("ANTHROPIC_API_KEY", "")
print(f"API Key: {'set ✓' if key else 'not set ✗'}")
```

```bash
python verify_setup.py
```

Expected output:

```
Python: 3.12.x
anthropic: 0.39.x ✓
API Key: set ✓
```

If all three pass, you are ready.

## Your First Agent Loop

Now write the most important code — the agent's core loop.

Create `agent.py`, starting with imports and configuration:

```python
import os
import sys
import subprocess
import anthropic

MODEL = "claude-sonnet-4-20250514"
SYSTEM = "你是一个有用的 AI 助手。你可以通过工具与计算机交互来完成任务。"
```

`MODEL` specifies which LLM to use. `SYSTEM` is the system prompt, telling the model who it is and what it can do.

### Define the Tool

The agent needs to know what tools it has available. Tools are described via JSON Schema:

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

This schema tells the model: you have a tool called `bash` that takes a `command` parameter and can execute shell commands. The model does not execute commands directly — it only says "I want to call bash with argument `ls -la`," and your code actually runs it.

> **Important**: The tool's `description` field is critically important. The model relies entirely on this text to decide when to use the tool. A vague description leads to misuse or non-use.

### Implement the Handler Function

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

This code does three things:

1. Uses `subprocess.run` to execute the command
2. Captures stdout and stderr
3. Sets a 30-second timeout to prevent commands from hanging

Note the return value is always a string — tool output is sent back to the LLM, and LLMs only understand text.

### The Core Loop

This is the heart of the entire agent — a while loop:

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

Let us walk through this loop step by step. It looks like only 30 lines, but every line is worth understanding.

**Step 1: Send messages to the LLM**

```python
response = client.messages.create(
    model=MODEL,
    max_tokens=4096,
    system=SYSTEM,
    messages=messages,
    tools=TOOLS,
)
```

You send the current message list (containing the user's request and all past interactions) to the LLM. You also pass the list of available tools — the model needs to know what it can use.

**Step 2: Save the response**

```python
messages.append({"role": "assistant", "content": response.content})
```

The LLM's response is appended to the message list. This is important — on the next call, the LLM sees its own previous responses and knows what it has already done.

**Step 3: Check whether a tool call is needed**

```python
if response.stop_reason != "tool_use":
    return
```

The LLM has two ways to stop:

- `"end_turn"`: The model considers the task complete and outputs a text response
- `"tool_use"`: The model wants to call a tool

If it is `"end_turn"`, the loop ends. If it is `"tool_use"`, we continue.

**Step 4: Execute the tool**

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

Iterate through each content block in the LLM's response, find tool-call requests, execute the corresponding handler function, and collect results. The `tool_use_id` links each result back to its request.

**Step 5: Return results and continue the loop**

```python
messages.append({"role": "user", "content": tool_results})
```

Tool results are appended to the message list with the `"user"` role (this is an API convention), then we loop back to the top. The LLM sees the tool results and decides what to do next — maybe call another tool, maybe declare the task complete.

> **Note**: This is the agent's entire secret. No deep learning magic, no complex state machine — just a while loop. The model decides what to do, you execute it, send back the result, the model decides again, you execute again... until the model says "done."

### Add the Entry Point

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

## Run Your First Agent

Save the file and run:

```bash
python agent.py "列出当前目录的文件，并告诉我一共有多少个"
```

You should see output similar to this:

```
You: 列出当前目录的文件，并告诉我一共有多少个
  [Tool: bash] ls -la
  total 16
  -rw-r--r--  1 user  staff  2048 Apr 17 10:00 agent.py
  -rw-r--r--  1 user  staff    42 Apr 17 10:00 requirements.txt
  -rw-r--r--  1 user  staff   512 Apr 17 10:00 verify_setup.py

Agent: 当前目录有 3 个文件：agent.py、requirements.txt 和 verify_setup.py。
```

Here is what happened:

1. You said "list the files and tell me how many"
2. The LLM analyzed your request and decided it needed the `bash` tool
3. The LLM output "I want to call bash with argument `ls -la`"
4. Your code executed `ls -la` and sent the output back to the LLM
5. The LLM saw the file listing, counted them, and answered "3 files"

Throughout this process, you wrote no logic like "if the user asks about file counts, run ls." The model decided on its own which tool and which arguments to use. This is the core value of an agent.

Try a more complex task:

```bash
python agent.py "创建一个名为 hello.py 的 Python 文件，内容是打印 Hello World，然后运行它"
```

Watch how the agent autonomously completes multiple steps — creating the file, writing the content, running it — all without your intervention.

## What Changed

This is the first chapter, so there is no "before" to compare. But let us record the starting point:

| State | Description |
|-------|-------------|
| Core file | `agent.py` (~90 lines) |
| Tool count | 1 (bash) |
| What the agent can do | Execute single or multiple bash commands |
| What the agent cannot do | Read/write files (must go through bash), remember conversations, plan tasks |

**Your MiniAgent's current architecture**:

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

In later chapters, this diagram will keep expanding. By Chapter 13, there will be 22 tools, sub-agents, team collaboration, and work isolation — but the core loop never changes.

## Try It Yourself

1. **Verify**: Run `python agent.py "What is the current operating system?"` and confirm the agent can call the bash tool and return results.

2. **Extend**: Modify the `handle_bash` function to print `>>> Executing: <command>` before each command runs. This helps you observe the agent's behavior more clearly.

3. **Explore**: Give the agent a task requiring multiple tool calls, such as "Create a directory called test_dir, create 3 files inside it, then list the directory contents." Observe how many loop iterations the agent executes. Think about this: what tells the LLM that the task is not yet complete?

## Summary

- The core of an **AI agent** is a loop: LLM thinks → calls tool → gets result → LLM thinks again
- **Agent = Model + Harness**: the model provides intelligence, the harness provides capability. This book builds the harness
- The agent's core loop is under 30 lines of code, but it is the foundation of the entire system
- Tools are described via JSON Schema; the model uses those descriptions to decide when to use which tool
- `stop_reason` is the loop's switch: `"tool_use"` means continue, `"end_turn"` means stop

In the next chapter, you give the agent more tools — so it no longer needs to go through bash just to read and write files.

## Further Reading

- [Anthropic Tool Use Documentation](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview) — Official documentation for tool calling
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) — A standardization protocol for agent tools
- Yao, S., et al. (2023). "ReAct: Synergizing Reasoning and Acting in Language Models." *ICLR 2023* — Theoretical foundation for the agent reason-act loop
