"""
MiniAgent — Team Manager
持久化队友系统：有名字、有角色、有独立 Agent 循环的长期运行实例。

通信机制：基于文件的邮箱系统 (.team/inbox/{name}.jsonl)

用法：
    tm = TeamManager()
    tm.spawn("reviewer", role="代码审查员", tools=[...], handlers={...}, system="...")
    tm.send("reviewer", "请审查 agent.py")
    messages = tm.read_inbox("lead")
"""

import os
import json
import time
import threading
from dataclasses import dataclass, field

TEAM_DIR = os.path.join(os.getcwd(), ".team")
INBOX_DIR = os.path.join(TEAM_DIR, "inbox")


@dataclass
class Teammate:
    """一个持久化队友的状态。"""
    name: str
    role: str
    status: str = "idle"  # idle | working | shutdown
    thread: threading.Thread | None = None
    created_at: float = field(default_factory=time.time)


class TeamManager:
    """管理持久化队友的生命周期和通信。"""

    def __init__(self):
        self._teammates: dict[str, Teammate] = {}
        self._lock = threading.Lock()
        os.makedirs(INBOX_DIR, exist_ok=True)

    def spawn(
        self,
        name: str,
        role: str,
        agent_loop_fn,
        tools: list,
        tool_handlers: dict,
        system: str,
    ) -> str:
        """创建并启动一个持久化队友。"""
        with self._lock:
            if name in self._teammates:
                existing = self._teammates[name]
                if existing.status != "shutdown":
                    return f"[error: 队友 '{name}' 已存在且正在运行]"

        # 创建邮箱文件
        inbox_path = os.path.join(INBOX_DIR, f"{name}.jsonl")
        if not os.path.exists(inbox_path):
            open(inbox_path, "w").close()

        teammate = Teammate(name=name, role=role, status="idle")

        def teammate_loop():
            """队友的主循环：检查邮箱 → 处理消息 → 回到 idle。"""
            import anthropic
            client = anthropic.Anthropic()
            messages = []
            role_system = f"{system}\n\n你的角色: {role}\n你的名字: {name}"

            while teammate.status != "shutdown":
                # 检查邮箱
                inbox_messages = self._read_inbox_raw(name)
                if not inbox_messages:
                    time.sleep(3)  # 空闲时轮询
                    continue

                teammate.status = "working"
                # 处理每条消息
                for msg in inbox_messages:
                    sender = msg.get("from", "unknown")
                    content = msg.get("content", "")
                    print(f"  [Team:{name}] 收到来自 {sender} 的消息")

                    messages.append({"role": "user", "content": content})

                    # 运行 agent loop（简化版，直接调用 API）
                    for _ in range(15):  # max turns per message
                        response = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=4096,
                            system=role_system,
                            messages=messages,
                            tools=tools,
                        )
                        messages.append({"role": "assistant", "content": response.content})

                        if response.stop_reason != "tool_use":
                            # 将回复发送回 sender
                            reply_parts = []
                            for block in response.content:
                                if hasattr(block, "text"):
                                    reply_parts.append(block.text)
                            if reply_parts:
                                reply = "\n".join(reply_parts)
                                self.send(sender, f"[来自 {name}] {reply}", from_name=name)
                                print(f"  [Team:{name}] 回复已发送给 {sender}")
                            break

                        # 执行工具
                        tool_results = []
                        for block in response.content:
                            if block.type == "tool_use":
                                handler = tool_handlers.get(block.name)
                                if handler is None:
                                    output = f"[error: 未知工具 {block.name}]"
                                else:
                                    output = handler(**block.input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": output,
                                })
                        messages.append({"role": "user", "content": tool_results})

                teammate.status = "idle"

            print(f"  [Team:{name}] 已关闭")

        thread = threading.Thread(target=teammate_loop, daemon=True)
        teammate.thread = thread

        with self._lock:
            self._teammates[name] = teammate

        thread.start()
        return f"队友 '{name}' ({role}) 已启动"

    def send(self, to_name: str, content: str, from_name: str = "lead") -> str:
        """向指定队友的邮箱发送消息。"""
        inbox_path = os.path.join(INBOX_DIR, f"{to_name}.jsonl")
        msg = {
            "from": from_name,
            "to": to_name,
            "content": content,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(inbox_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        return f"消息已发送给 {to_name}"

    def _read_inbox_raw(self, name: str) -> list[dict]:
        """读取并清空邮箱（原子操作）。"""
        inbox_path = os.path.join(INBOX_DIR, f"{name}.jsonl")
        if not os.path.exists(inbox_path):
            return []
        with self._lock:
            with open(inbox_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if not lines:
                return []
            # 清空邮箱
            with open(inbox_path, "w", encoding="utf-8") as f:
                pass
        messages = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return messages

    def read_inbox(self, name: str = "lead") -> str:
        """读取指定邮箱的所有消息（供 Lead Agent 使用）。"""
        messages = self._read_inbox_raw(name)
        if not messages:
            return f"邮箱 '{name}' 为空"
        lines = []
        for msg in messages:
            lines.append(f"[{msg.get('timestamp', '?')}] {msg.get('from', '?')}: {msg.get('content', '')}")
        return "\n".join(lines)

    def shutdown(self, name: str) -> str:
        """关闭指定队友。"""
        with self._lock:
            teammate = self._teammates.get(name)
        if teammate is None:
            return f"[error: 队友 '{name}' 不存在]"
        teammate.status = "shutdown"
        return f"队友 '{name}' 正在关闭..."

    def list_teammates(self) -> str:
        """列出所有队友状态。"""
        with self._lock:
            teammates = list(self._teammates.values())
        if not teammates:
            return "没有队友"
        lines = []
        for t in teammates:
            elapsed = time.time() - t.created_at
            lines.append(f"  {t.name}: [{t.status}] {t.role} (运行 {elapsed:.0f}s)")
        return "\n".join(lines)


# --- 工具 Schema ---
SPAWN_TOOL = {
    "name": "spawn",
    "description": (
        "创建并启动一个持久化队友。队友有自己的名字、角色和独立的 Agent 循环。"
        "可通过 send 工具向队友发送任务，通过 inbox 工具查看回复。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "队友名称（唯一标识）"},
            "role": {"type": "string", "description": "队友角色描述（如'代码审查员'、'测试工程师'）"},
        },
        "required": ["name", "role"],
    },
}

SEND_TOOL = {
    "name": "send",
    "description": "向指定队友发送消息或任务指令。",
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "目标队友名称"},
            "content": {"type": "string", "description": "消息内容"},
        },
        "required": ["to", "content"],
    },
}

INBOX_TOOL = {
    "name": "inbox",
    "description": "查看我的邮箱。队友的回复会出现在这里。",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

TEAM_STATUS_TOOL = {
    "name": "team_status",
    "description": "查看所有队友的状态。",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

TEAM_TOOLS = [SPAWN_TOOL, SEND_TOOL, INBOX_TOOL, TEAM_STATUS_TOOL]
