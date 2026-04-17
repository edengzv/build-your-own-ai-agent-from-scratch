# Chapter 2: 工具调用

> **Motto**: "增加一个工具，只需增加一个处理函数"

> 上一章的 Agent 只有 bash 一个工具，什么都靠 shell 命令绕路。本章你将引入工具分发机制——一个字典映射 `{工具名: 处理函数}`，并添加三个文件操作工具。核心循环不变，能力翻四倍。

## The Problem

上一章的 Agent 能工作，但它只有一把锤子——bash。看看它读文件时的样子：

```
You: 读取 agent.py 的前 5 行
  [Tool: bash] head -5 agent.py
  """
  MiniAgent — Chapter 1: 你好，Agent
  一个不到 30 行核心代码的 AI Agent。
  ...
```

它在用 `head` 命令读文件。再看看它写文件：

```
You: 创建一个 config.json，内容是 {"debug": true}
  [Tool: bash] echo '{"debug": true}' > config.json
```

用 `echo >` 写文件。这有三个问题：

1. **不安全**：`echo` + shell 重定向容易出错，特殊字符需要转义
2. **不可靠**：多行内容、Unicode 字符、嵌套引号都可能出问题
3. **无错误处理**：文件不存在？权限不够？`echo` 不会告诉你

更严重的是，所有工具调用都走 `handle_bash(**block.input)`——如果 LLM 返回了一个不是 bash 的工具名，代码会直接崩溃。

我们需要一个通用的工具分发机制，以及专门的文件操作工具。

## The Solution

解决方案分两部分：

1. **工具分发映射**：一个字典 `{tool_name: handler_function}`，Agent 循环根据工具名查字典调用对应函数
2. **专用文件工具**：`read_file`、`write_file`、`edit_file`，每个都有安全路径检查

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

关键洞察：**循环不变，只改分发逻辑**。Agent 循环不需要知道有哪些工具——它只需要一个字典来查找处理函数。

## 工具分发映射

回顾上一章的循环，工具执行部分是这样的：

```python
# Chapter 1: 硬编码 bash
for block in response.content:
    if block.type == "tool_use":
        output = handle_bash(**block.input)  # 只能调用 bash
```

如果我们添加更多工具，难道要写一堆 `if/elif`？

```python
# 这样做很丑陋，也不可扩展
if block.name == "bash":
    output = handle_bash(**block.input)
elif block.name == "read_file":
    output = handle_read_file(**block.input)
elif block.name == "write_file":
    output = handle_write_file(**block.input)
```

更好的方式是一个字典：

```python
# NEW: 工具分发映射
TOOL_HANDLERS = {
    "bash": handle_bash,
    "read_file": handle_read_file,
    "write_file": handle_write_file,
    "edit_file": handle_edit_file,
}
```

循环中的调用变成：

```python
handler = TOOL_HANDLERS.get(block.name)  # CHANGED
if handler is None:
    output = f"[error: 未知工具 {block.name}]"
else:
    output = handler(**block.input)
```

这就是整个分发机制。以后添加新工具，只需要：

1. 写一个 `handle_xxx()` 函数
2. 在 `TOOL_HANDLERS` 里加一行
3. 在 `TOOLS` 列表里加一个 schema

循环本身永远不需要改。这个模式在后续章节中会反复出现。

> **Tip**: `TOOL_HANDLERS` 是一个注册表模式（Registry Pattern）。在 Agent 开发中，这是管理工具最常见的方式。几乎所有 Agent 框架内部都有类似的映射表。

## 安全路径检查

在实现文件操作之前，先解决一个安全问题。Agent 能执行文件操作意味着它可能读写任何文件——包括 `/etc/passwd` 或你的私钥。

引入 `safe_path()` 函数，限制所有文件操作在工作目录内：

```python
WORKSPACE = os.getcwd()  # NEW

def safe_path(path: str) -> str:  # NEW
    """确保路径在工作目录内，防止路径遍历攻击。"""
    resolved = os.path.realpath(os.path.join(WORKSPACE, path))
    if not resolved.startswith(os.path.realpath(WORKSPACE)):
        raise ValueError(f"路径 {path} 超出工作目录范围")
    return resolved
```

这段代码做了什么：

1. 将相对路径转换为绝对路径
2. 用 `os.path.realpath` 解析所有符号链接和 `..`
3. 检查结果路径是否以工作目录开头

如果有人（或 LLM）试图访问 `../../etc/passwd`，`safe_path` 会抛出异常。

> **Warning**: `safe_path` 是最基本的安全措施，不能替代完整的沙箱。Chapter 14 会构建更严格的安全层。但在这个阶段，它足以防止最常见的路径遍历攻击。

## 实现文件操作工具

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

注意返回值：

- 成功时返回文件内容（纯文本字符串）
- 失败时返回以 `[error: ...]` 开头的字符串

**为什么不抛异常？** 因为工具的输出会被送回 LLM。如果你抛异常，Agent 循环会崩溃。如果你返回错误信息，LLM 能理解发生了什么并尝试修复——比如创建不存在的文件，或换一个路径。

这是工具设计的一个重要原则：**工具永远返回字符串，永远不抛异常**。错误也是信息。

对应的工具 schema：

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

`os.makedirs(..., exist_ok=True)` 自动创建不存在的父目录。这很方便——LLM 可以直接写 `src/utils/helper.py` 而不用先 `mkdir -p src/utils`。

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

`edit_file` 的设计有一个关键约束：**old_string 必须唯一匹配**。为什么？

- 0 次匹配：替换没有生效，这是 bug
- 1 次匹配：精确替换，安全
- 多次匹配：可能替换了不该替换的地方，危险

这个约束迫使 LLM 提供足够精确的上下文来定位修改点，大幅降低误编辑的风险。

> **Note**: 为什么不用 `sed` 或正则表达式？因为 LLM 生成正确的正则表达式比生成精确的字符串匹配更难出错。LLM 擅长复制粘贴精确文本，不擅长写复杂的正则。工具设计应该迎合 LLM 的能力特点。

## 工具设计原则

在添加了四个工具之后，让我们总结一下好工具的特征：

**1. 单一职责**

每个工具做一件事。`read_file` 只读，`write_file` 只写。不要做一个 `file_manager` 工具接受 `action: "read" | "write" | "edit"` 参数——这让 LLM 的决策更复杂，也更容易出错。

**2. 清晰的 Schema**

`description` 字段决定了 LLM 何时选用这个工具。参数名要自解释：`path` 而不是 `p`，`command` 而不是 `cmd`。

**3. 友好的错误信息**

```python
# 好：告诉 LLM 发生了什么，它可以修复
return "[error: 文件不存在: config.json]"

# 差：LLM 看到这个无法采取行动
return "[error]"
```

**4. 安全边界**

每个涉及系统操作的工具都应该有安全检查。`safe_path` 限制文件范围，`timeout` 限制执行时间。

**5. 字符串进，字符串出**

工具的输入来自 LLM（JSON 解析后的参数），输出送回 LLM（纯文本）。两端都是字符串。不要返回复杂对象。

## 更新后的 Agent 循环

让我们看看循环中实际变化的部分：

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

变化只有两处：

1. `handle_bash(**block.input)` → `TOOL_HANDLERS.get(block.name)` + `handler(**block.input)`
2. 添加了未知工具的错误处理

循环的结构完全没变。`while True` → LLM 调用 → 检查 stop_reason → 执行工具 → 送回结果。这就是 Chapter 1 中说的"核心循环始终不变"。

保存并运行：

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

注意 Agent 选择了 `write_file` 和 `read_file` 而不是 `bash echo >` 和 `bash cat`。LLM 根据工具描述，自动选择了更合适的工具。

## What Changed

| Before This Chapter | After This Chapter |
|--------------------|--------------------|
| 1 个工具 (bash) | 4 个工具 (bash, read_file, write_file, edit_file) |
| 硬编码 `handle_bash()` 调用 | 通用分发映射 `TOOL_HANDLERS{}` |
| 文件操作靠 shell 命令 | 专用文件工具，安全路径检查 |
| 未知工具会崩溃 | 返回错误信息，Agent 可以恢复 |
| ~90 行代码 | ~200 行代码 |

**Cumulative capability**: 你的 MiniAgent 现在能执行 bash 命令、安全地读写文件、精确地编辑文件。

## Try It Yourself

1. **Verify**: 运行 `python miniagent/agent.py "读取 miniagent/agent.py 并告诉我有多少行"`，确认 `read_file` 工具正常工作。

2. **Extend**: 添加一个 `list_dir` 工具，接受 `path` 参数，返回目录内容。提示：实现 `handle_list_dir()`，添加到 `TOOL_HANDLERS`，添加 schema 到 `TOOLS`。

3. **Explore**: 尝试让 Agent 访问工作目录之外的文件（比如 `/etc/hosts`）。观察 `safe_path` 如何拦截。思考：如果 Agent 通过 `bash` 工具执行 `cat /etc/hosts`，`safe_path` 能拦截吗？（剧透：不能。这是 Chapter 14 要解决的问题。）

## Summary

- **工具分发映射** `TOOL_HANDLERS` 是管理多工具的核心模式：字典查找替代 if/elif
- 添加新工具的三步：写 handler → 加入 TOOL_HANDLERS → 添加 schema
- **Agent 循环不变**：工具再多，循环结构不需要修改
- **safe_path()** 提供基本的路径安全保障，限制文件操作在工作目录内
- 工具设计原则：单一职责、清晰 schema、友好错误、安全边界、字符串进出
- **edit_file 的唯一匹配约束**迫使 LLM 提供精确的上下文，降低误编辑风险

下一章，你将让 Agent 拥有记忆——从一次性执行变成能连续工作的交互式助手。

## Further Reading

- [JSON Schema Specification](https://json-schema.org/) — 工具 schema 的标准规范
- [Anthropic Tool Use Best Practices](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview) — 工具设计的官方建议
- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal) — 路径遍历攻击的安全参考
