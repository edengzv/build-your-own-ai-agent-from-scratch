<!-- Translated from: ch02-tool-use.md -->

# Chapter 2: Tool Dispatch

> **Motto**: "Adding a tool means adding a single handler function."

> The agent from the previous chapter had only one tool — bash — and had to route everything through shell commands. In this chapter, you introduce a tool dispatch mechanism: a dictionary mapping `{tool_name: handler_function}`, plus three dedicated file-operation tools. The core loop stays the same; capability quadruples.

![Conceptual: AI brain dispatching to multiple tools](images/ch02/fig-02-01-concept.png)

*Figure 2-1. Tool dispatch: one brain, many hands — each tool extends the agent's reach.*
## The Problem

The agent from Chapter 1 works, but it only has one hammer — bash. Watch it read a file:

```
You: 读取 agent.py 的前 5 行
  [Tool: bash] head -5 agent.py
  """
  MiniAgent — Chapter 1: 你好，Agent
  一个不到 30 行核心代码的 AI Agent。
  ...
```

It is using the `head` command to read a file. Now watch it write a file:

```
You: 创建一个 config.json，内容是 {"debug": true}
  [Tool: bash] echo '{"debug": true}' > config.json
```

Using `echo >` to write a file. This has three problems:

1. **Unsafe**: `echo` plus shell redirection is error-prone; special characters need escaping
2. **Unreliable**: Multi-line content, Unicode characters, and nested quotes can all break
3. **No error handling**: File does not exist? Insufficient permissions? `echo` will not tell you

Worse still, every tool call goes through `handle_bash(**block.input)` — if the LLM returns a tool name that is not bash, the code crashes outright.

We need a general-purpose tool dispatch mechanism, plus dedicated file-operation tools.

## The Solution

The solution has two parts:

1. **Tool dispatch mapping**: A dictionary `{tool_name: handler_function}`. The agent loop looks up the tool name in the dictionary and calls the corresponding function
2. **Dedicated file tools**: `read_file`, `write_file`, `edit_file`, each with safe path checking

```
┌──────────────────────────────┐
│        agent_loop()          │
│  ┌────────────┐              │
│  │    LLM     │              │
│  └─────┬──────┘              │
│        ↓                     │
│  ┌────────────────────────┐  │
│  │   TOOL_HANDLERS { }   │  │  ← NEW: 分发映射
│  │  ┌──────┐ ┌─────────┐ │  │
│  │  │ bash │ │read_file│ │  │
│  │  └──────┘ └─────────┘ │  │
│  │  ┌──────────┐ ┌──────┐│  │
│  │  │write_file│ │ edit ││  │
│  │  └──────────┘ └──────┘│  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

The key insight: **the loop does not change — only the dispatch logic does**. The agent loop does not need to know which tools exist; it only needs a dictionary to look up handler functions.

## The Tool Dispatch Mapping

Recall how the tool-execution portion of the loop looked in Chapter 1:

```python
# Chapter 1: 硬编码 bash
for block in response.content:
    if block.type == "tool_use":
        output = handle_bash(**block.input)  # 只能调用 bash
```

If we add more tools, should we write a chain of `if/elif` statements?

```python
# 这样做很丑陋，也不可扩展
if block.name == "bash":
    output = handle_bash(**block.input)
elif block.name == "read_file":
    output = handle_read_file(**block.input)
elif block.name == "write_file":
    output = handle_write_file(**block.input)
```

A dictionary is better:

```python
# NEW: 工具分发映射
TOOL_HANDLERS = {
    "bash": handle_bash,
    "read_file": handle_read_file,
    "write_file": handle_write_file,
    "edit_file": handle_edit_file,
}
```

And the call inside the loop becomes:

```python
handler = TOOL_HANDLERS.get(block.name)  # CHANGED
if handler is None:
    output = f"[error: 未知工具 {block.name}]"
else:
    output = handler(**block.input)
```

That is the entire dispatch mechanism. From now on, adding a new tool requires only three steps:

1. Write a `handle_xxx()` function
2. Add one line to `TOOL_HANDLERS`
3. Add one schema to the `TOOLS` list

The loop itself never needs to change. This pattern will reappear throughout the rest of the book.

> **Tip**: `TOOL_HANDLERS` is a Registry Pattern. In agent development, this is the most common way to manage tools. Nearly every agent framework has a similar mapping table under the hood.

## Safe Path Checking

Before implementing file operations, let us address a security concern. An agent that can perform file operations could read or write any file — including `/etc/passwd` or your private keys.

We introduce a `safe_path()` function that restricts all file operations to within the working directory:

```python
WORKSPACE = os.getcwd()  # NEW

def safe_path(path: str) -> str:  # NEW
    """确保路径在工作目录内，防止路径遍历攻击。"""
    resolved = os.path.realpath(os.path.join(WORKSPACE, path))
    if not resolved.startswith(os.path.realpath(WORKSPACE)):
        raise ValueError(f"路径 {path} 超出工作目录范围")
    return resolved
```

Here is what this code does:

1. Converts the relative path to an absolute path
2. Uses `os.path.realpath` to resolve all symlinks and `..` components
3. Checks that the resulting path starts with the working directory

If someone (or the LLM) tries to access `../../etc/passwd`, `safe_path` raises an exception.

> **Warning**: `safe_path` is the most basic security measure and is no substitute for a full sandbox. Chapter 14 builds a much stricter security layer. But at this stage, it is enough to prevent the most common path-traversal attacks.

## Implementing the File-Operation Tools

### read_file

```python
def handle_read_file(path: str) -> str:  # NEW
    """读取文件内容。"""
    try:
        file_path = safe_path(path)
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except ValueError as e:
        return f"[error: {e}]"
    except FileNotFoundError:
        return f"[error: 文件不存在: {path}]"
    except Exception as e:
        return f"[error: {e}]"
```

Notice the return values:

- On success, it returns the file contents (a plain-text string)
- On failure, it returns a string starting with `[error: ...]`

**Why not raise an exception?** Because the tool's output is sent back to the LLM. If you raise an exception, the agent loop crashes. If you return an error message, the LLM can understand what happened and try to fix it — for example, by creating a missing file or trying a different path.

This is an important principle of tool design: **tools always return strings, never raise exceptions**. Errors are information too.

The corresponding tool schema:

```python
{
    "name": "read_file",
    "description": "读取指定文件的完整内容。适用于查看代码、配置文件、文档等。",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "要读取的文件路径（相对于工作目录）",
            }
        },
        "required": ["path"],
    },
}
```

### write_file

```python
def handle_write_file(path: str, content: str) -> str:  # NEW
    """写入文件内容。"""
    try:
        file_path = safe_path(path)
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"已写入 {path} ({len(content)} 字符)"
    except ValueError as e:
        return f"[error: {e}]"
    except Exception as e:
        return f"[error: {e}]"
```

`os.makedirs(..., exist_ok=True)` automatically creates missing parent directories. This is convenient — the LLM can write directly to `src/utils/helper.py` without first running `mkdir -p src/utils`.

### edit_file

```python
def handle_edit_file(path: str, old_string: str, new_string: str) -> str:  # NEW
    """通过查找替换编辑文件。"""
    try:
        file_path = safe_path(path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        count = content.count(old_string)
        if count == 0:
            return "[error: 未找到要替换的文本]"
        if count > 1:
            return f"[error: 找到 {count} 处匹配，需要唯一匹配]"

        new_content = content.replace(old_string, new_string, 1)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"已编辑 {path}"
    except ValueError as e:
        return f"[error: {e}]"
    except FileNotFoundError:
        return f"[error: 文件不存在: {path}]"
    except Exception as e:
        return f"[error: {e}]"
```

`edit_file` has one critical constraint: **old_string must match exactly once**. Why?

- 0 matches: The replacement did not take effect — that is a bug
- 1 match: Precise replacement — safe
- Multiple matches: You might replace something you should not have — dangerous

This constraint forces the LLM to provide enough surrounding context to uniquely locate the edit point, dramatically reducing the risk of accidental edits.

> **Note**: Why not use `sed` or regular expressions? Because the LLM is more likely to make mistakes generating correct regex than generating an exact string match. LLMs are good at copy-pasting precise text; they are not good at writing complex regex. Tool design should play to the LLM's strengths.

## Tool Design Principles

Now that we have four tools, let us summarize the characteristics of a well-designed tool:

**1. Single Responsibility**

Each tool does one thing. `read_file` only reads, `write_file` only writes. Do not build a single `file_manager` tool that takes an `action: "read" | "write" | "edit"` parameter — that makes the LLM's decision-making more complex and more error-prone.

**2. Clear Schema**

The `description` field determines when the LLM will choose a tool. Parameter names should be self-explanatory: `path` instead of `p`, `command` instead of `cmd`.

**3. Friendly Error Messages**

```python
# 好：告诉 LLM 发生了什么，它可以修复
return "[error: 文件不存在: config.json]"

# 差：LLM 看到这个无法采取行动
return "[error]"
```

**4. Security Boundaries**

Every tool that touches the system should include safety checks. `safe_path` restricts file scope; `timeout` limits execution time.

**5. Strings In, Strings Out**

A tool's input comes from the LLM (parameters parsed from JSON); its output goes back to the LLM (plain text). Both ends are strings. Do not return complex objects.

## The Updated Agent Loop

Let us look at the parts of the loop that actually changed:

```python
def agent_loop(messages: list) -> None:
    client = anthropic.Anthropic()

    while True:
        response = client.messages.create(
            model=MODEL, max_tokens=4096, system=SYSTEM,
            messages=messages, tools=TOOLS,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nAgent: {block.text}")
            return

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                handler = TOOL_HANDLERS.get(block.name)  # CHANGED: 分发映射
                if handler is None:                        # NEW: 未知工具处理
                    output = f"[error: 未知工具 {block.name}]"
                else:
                    print(f"  [Tool: {block.name}] {_summarize_input(block)}")
                    output = handler(**block.input)         # CHANGED: 通用调用
                    print(f"  {output[:200]}{'...' if len(output) > 200 else ''}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })

        messages.append({"role": "user", "content": tool_results})
```

Only two things changed:

1. `handle_bash(**block.input)` became `TOOL_HANDLERS.get(block.name)` + `handler(**block.input)`
2. Error handling for unknown tools was added

The structure of the loop is completely unchanged. `while True` -> LLM call -> check stop_reason -> execute tools -> return results. This is what Chapter 1 meant by "the core loop never changes."

Save and run:

```bash
python miniagent/agent.py "创建一个 hello.py 文件，内容是打印 Hello World，然后读取确认"
```

```
You: 创建一个 hello.py 文件，内容是打印 Hello World，然后读取确认
  [Tool: write_file] hello.py
  已写入 hello.py (21 字符)
  [Tool: read_file] hello.py
  print("Hello World")

Agent: 已创建 hello.py 文件，内容是 `print("Hello World")`。我已经读取确认，文件内容正确。
```

Notice that the agent chose `write_file` and `read_file` instead of `bash echo >` and `bash cat`. Based on the tool descriptions, the LLM automatically selected the more appropriate tools.

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 1 tool (bash) | 4 tools (bash, read_file, write_file, edit_file) |
| Hardcoded `handle_bash()` call | Generic dispatch mapping `TOOL_HANDLERS{}` |
| File operations via shell commands | Dedicated file tools with safe path checking |
| Unknown tool names crash the agent | Error message returned; agent can recover |
| ~90 lines of code | ~200 lines of code |

**Cumulative capability**: Your MiniAgent can now execute bash commands, safely read and write files, and precisely edit files.

## Try It Yourself

1. **Verify**: Run `python miniagent/agent.py "读取 miniagent/agent.py 并告诉我有多少行"` and confirm that the `read_file` tool works correctly.

2. **Extend**: Add a `list_dir` tool that takes a `path` parameter and returns the directory contents. Hint: implement `handle_list_dir()`, add it to `TOOL_HANDLERS`, and add a schema to `TOOLS`.

3. **Explore**: Try to make the agent access a file outside the working directory (for example, `/etc/hosts`). Observe how `safe_path` blocks it. Then think: if the agent runs `cat /etc/hosts` through the `bash` tool, can `safe_path` block that? (Spoiler: it cannot. That is a problem Chapter 14 addresses.)

## Summary

- The **tool dispatch mapping** `TOOL_HANDLERS` is the core pattern for managing multiple tools: dictionary lookup replaces if/elif chains
- Adding a new tool takes three steps: write a handler -> add it to TOOL_HANDLERS -> add a schema
- **The agent loop does not change**: No matter how many tools you add, the loop structure stays the same
- **safe_path()** provides basic path-safety guarantees, restricting file operations to the working directory
- Tool design principles: single responsibility, clear schema, friendly errors, security boundaries, strings in and out
- **edit_file's unique-match constraint** forces the LLM to provide precise context, reducing the risk of accidental edits

In the next chapter, you give the agent memory — transforming it from a one-shot executor into an interactive assistant that can work continuously.

## Further Reading

- [JSON Schema Specification](https://json-schema.org/) — The standard specification for tool schemas
- [Anthropic Tool Use Best Practices](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview) — Official guidance on tool design
- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal) — Security reference for path-traversal attacks
