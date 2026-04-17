"""
security — 安全与权限模块

提供路径沙箱、命令分级、人类确认机制和基于角色的权限控制。

核心组件：
- Sandbox: 限制文件操作在指定目录内
- classify_command: 将 bash 命令分为 safe / restricted / dangerous
- ConfirmationGate: 危险操作需要人类确认
- make_security_wrapper: 为工具处理函数添加安全包装

用法：
    sandbox = Sandbox("/path/to/workspace")
    gate = ConfirmationGate()
    safe_bash = make_security_wrapper(handle_bash, "bash", sandbox, gate)
"""

import os
import re


# ── 路径沙箱 ─────────────────────────────────────────────────

class Sandbox:
    """将文件操作限制在允许的目录内。"""

    def __init__(self, base_dir: str):
        self.base_dir = os.path.realpath(base_dir)
        self._allowed: list[str] = [self.base_dir]

    def add_allowed_dir(self, path: str) -> None:
        """添加额外允许的目录（例如 worktree 路径）。"""
        real = os.path.realpath(path)
        if real not in self._allowed:
            self._allowed.append(real)

    def check_path(self, path: str) -> str:
        """检查路径是否在允许范围内，返回绝对路径。

        如果路径是相对的，基于 base_dir 解析。
        如果超出所有允许目录，抛出 ValueError。
        """
        if os.path.isabs(path):
            resolved = os.path.realpath(path)
        else:
            resolved = os.path.realpath(os.path.join(self.base_dir, path))

        for allowed in self._allowed:
            if resolved.startswith(allowed):
                return resolved
        raise ValueError(f"路径 {path} 超出允许范围")

    def is_allowed(self, path: str) -> bool:
        """检查路径是否允许（不抛异常版本）。"""
        try:
            self.check_path(path)
            return True
        except ValueError:
            return False


# ── 命令分级 ─────────────────────────────────────────────────

# 危险命令模式——匹配则需要人类确认
DANGEROUS_PATTERNS: list[str] = [
    r"\brm\s+(-[a-zA-Z]*f|-[a-zA-Z]*r|--force|--recursive)",  # rm -rf
    r"\brm\s+-rf\b",
    r"\bsudo\b",
    r"\bmkfs\b",
    r"\bdd\s+",
    r"\b(chmod|chown)\s+(-R|--recursive)",
    r"\bgit\s+push\s+.*--force",
    r"\bgit\s+reset\s+--hard",
    r"\b>\s*/dev/",
    r"\bcurl\s+.*\|\s*(bash|sh)\b",
    r"\bwget\s+.*\|\s*(bash|sh)\b",
]

# 受限命令模式——提示但不强制确认
RESTRICTED_PATTERNS: list[str] = [
    r"\bgit\s+push\b",
    r"\bgit\s+merge\b",
    r"\bgit\s+rebase\b",
    r"\bnpm\s+publish\b",
    r"\bpip\s+install\b",
    r"\bbrew\s+install\b",
]

_dangerous_re = [re.compile(p) for p in DANGEROUS_PATTERNS]
_restricted_re = [re.compile(p) for p in RESTRICTED_PATTERNS]


def classify_command(command: str) -> str:
    """将 bash 命令分类为 safe / restricted / dangerous。

    Returns:
        "dangerous"  —— 需要确认才能执行
        "restricted" —— 提示用户但不阻塞
        "safe"       —— 直接执行
    """
    for pattern in _dangerous_re:
        if pattern.search(command):
            return "dangerous"
    for pattern in _restricted_re:
        if pattern.search(command):
            return "restricted"
    return "safe"


# ── 权限模型 ─────────────────────────────────────────────────

class PermissionLevel:
    """工具权限级别。"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DANGEROUS = "dangerous"


# 工具名 → 所需权限级别
TOOL_PERMISSIONS: dict[str, str] = {
    "read_file": PermissionLevel.READ,
    "write_file": PermissionLevel.WRITE,
    "edit_file": PermissionLevel.WRITE,
    "bash": PermissionLevel.EXECUTE,
    "spawn": PermissionLevel.DANGEROUS,
    "shutdown_request": PermissionLevel.DANGEROUS,
}

# 角色 → 允许的权限级别集合
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "lead": {PermissionLevel.READ, PermissionLevel.WRITE,
             PermissionLevel.EXECUTE, PermissionLevel.DANGEROUS},
    "teammate": {PermissionLevel.READ, PermissionLevel.WRITE,
                 PermissionLevel.EXECUTE},
    "reviewer": {PermissionLevel.READ, PermissionLevel.EXECUTE},
}


def check_tool_permission(tool_name: str, role: str = "lead") -> bool:
    """检查指定角色是否有权使用某工具。"""
    required = TOOL_PERMISSIONS.get(tool_name)
    if required is None:
        return True  # 未列出的工具默认允许
    allowed = ROLE_PERMISSIONS.get(role, set())
    return required in allowed


# ── 人类确认机制 ─────────────────────────────────────────────

class ConfirmationGate:
    """拦截危险操作，请求人类确认。"""

    def __init__(self):
        self._auto_approve: set[str] = set()

    def needs_confirmation(self, tool_name: str, tool_input: dict) -> bool:
        """判断本次调用是否需要确认。"""
        if tool_name in self._auto_approve:
            return False
        if tool_name == "bash":
            level = classify_command(tool_input.get("command", ""))
            return level == "dangerous"
        return False

    def request_confirmation(self, tool_name: str, tool_input: dict) -> bool:
        """向用户请求确认。返回 True 表示批准。"""
        cmd = tool_input.get("command", str(tool_input))
        print(f"\n{'='*50}")
        print(f"  ⚠️  危险操作需要确认")
        print(f"  工具: {tool_name}")
        print(f"  输入: {cmd[:200]}")
        print(f"{'='*50}")
        try:
            answer = input("  允许执行？(y/n/always): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return False
        if answer == "always":
            self._auto_approve.add(tool_name)
            return True
        return answer in ("y", "yes")

    def auto_approve(self, tool_name: str) -> None:
        """标记某工具为自动批准。"""
        self._auto_approve.add(tool_name)


# ── 输入清理 ─────────────────────────────────────────────────

def sanitize_tool_input(tool_input: dict) -> dict:
    """基础输入清理：去除前后空白、限制长度。"""
    cleaned = {}
    for key, value in tool_input.items():
        if isinstance(value, str):
            value = value.strip()
            if len(value) > 100_000:
                value = value[:100_000] + "\n... [truncated]"
        cleaned[key] = value
    return cleaned


# ── 安全包装器 ───────────────────────────────────────────────

def make_security_wrapper(handler, tool_name: str,
                          sandbox: Sandbox | None = None,
                          gate: ConfirmationGate | None = None,
                          role: str = "lead"):
    """为工具处理函数添加安全层。

    包装逻辑：
    1. 权限检查——角色是否有权使用此工具
    2. 输入清理——去除多余空白、截断超长输入
    3. 确认机制——危险操作请求人类批准
    4. 调用原始 handler

    Args:
        handler: 原始工具处理函数
        tool_name: 工具名称
        sandbox: 路径沙箱（可选）
        gate: 确认门（可选）
        role: 调用者角色

    Returns:
        包装后的处理函数
    """
    def wrapper(**kwargs):
        # 1. 权限检查
        if not check_tool_permission(tool_name, role):
            return f"[error: 角色 '{role}' 无权使用工具 '{tool_name}']"

        # 2. 输入清理
        cleaned = sanitize_tool_input(kwargs)

        # 3. 确认机制
        if gate is not None and gate.needs_confirmation(tool_name, cleaned):
            if not gate.request_confirmation(tool_name, cleaned):
                return "[操作已被用户拒绝]"

        # 4. 调用原始 handler
        return handler(**cleaned)

    return wrapper
