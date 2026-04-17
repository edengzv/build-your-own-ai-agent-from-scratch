"""
MiniAgent — Protocols
结构化的团队通信协议：请求-响应模式。

支持的协议：
- shutdown: 安全关闭队友（请求 → 完成当前工作 → 确认）
- plan: 方案审批（提交方案 → 审查 → 批准/拒绝）

协议存储：.team/protocols/{request_id}.json
"""

import os
import json
import time
import uuid

PROTOCOLS_DIR = os.path.join(os.getcwd(), ".team", "protocols")


def _ensure_dir():
    os.makedirs(PROTOCOLS_DIR, exist_ok=True)


def _request_path(request_id: str) -> str:
    return os.path.join(PROTOCOLS_DIR, f"{request_id}.json")


def _save_request(req: dict) -> None:
    _ensure_dir()
    with open(_request_path(req["id"]), "w", encoding="utf-8") as f:
        json.dump(req, f, ensure_ascii=False, indent=2)


def _load_request(request_id: str) -> dict | None:
    path = _request_path(request_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Shutdown 协议 ---

def create_shutdown_request(target_name: str, reason: str = "") -> str:
    """Lead 创建一个安全关闭请求。"""
    _ensure_dir()
    request_id = f"shutdown_{uuid.uuid4().hex[:8]}"
    req = {
        "id": request_id,
        "type": "shutdown",
        "target": target_name,
        "reason": reason,
        "status": "pending",  # pending → approved → completed | rejected
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "responded_at": "",
        "response_note": "",
    }
    _save_request(req)
    return f"关闭请求 {request_id} 已创建，等待 {target_name} 响应"


def respond_shutdown(request_id: str, approve: bool, note: str = "") -> str:
    """队友响应关闭请求。"""
    req = _load_request(request_id)
    if req is None:
        return f"[error: 请求 {request_id} 不存在]"
    if req["type"] != "shutdown":
        return f"[error: {request_id} 不是关闭请求]"
    if req["status"] != "pending":
        return f"[error: 请求已处理，状态: {req['status']}]"

    req["status"] = "approved" if approve else "rejected"
    req["responded_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    req["response_note"] = note
    _save_request(req)

    action = "批准" if approve else "拒绝"
    return f"队友已{action}关闭请求 {request_id}"


# --- Plan 协议 ---

def create_plan_request(author: str, plan_summary: str, plan_details: str = "") -> str:
    """队友提交一个方案等待 Lead 审批。"""
    _ensure_dir()
    request_id = f"plan_{uuid.uuid4().hex[:8]}"
    req = {
        "id": request_id,
        "type": "plan",
        "author": author,
        "summary": plan_summary,
        "details": plan_details,
        "status": "pending",  # pending → approved | rejected
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "reviewed_at": "",
        "reviewer_note": "",
    }
    _save_request(req)
    return f"方案 {request_id} 已提交，等待审批"


def review_plan(request_id: str, approve: bool, note: str = "") -> str:
    """Lead 审批方案。"""
    req = _load_request(request_id)
    if req is None:
        return f"[error: 方案 {request_id} 不存在]"
    if req["type"] != "plan":
        return f"[error: {request_id} 不是方案请求]"
    if req["status"] != "pending":
        return f"[error: 方案已处理，状态: {req['status']}]"

    req["status"] = "approved" if approve else "rejected"
    req["reviewed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    req["reviewer_note"] = note
    _save_request(req)

    action = "批准" if approve else "拒绝"
    return f"方案 {request_id} 已{action}"


# --- 通用查询 ---

def list_requests(status: str = "", req_type: str = "") -> str:
    """列出协议请求。"""
    _ensure_dir()
    results = []
    for fname in sorted(os.listdir(PROTOCOLS_DIR)):
        if not fname.endswith(".json"):
            continue
        req = _load_request(fname.replace(".json", ""))
        if req is None:
            continue
        if status and req["status"] != status:
            continue
        if req_type and req["type"] != req_type:
            continue
        results.append(req)

    if not results:
        return "没有匹配的协议请求"

    lines = []
    for req in results:
        if req["type"] == "shutdown":
            lines.append(f"  [{req['status']}] {req['id']}: 关闭 {req['target']}")
        elif req["type"] == "plan":
            lines.append(f"  [{req['status']}] {req['id']}: {req['author']} 的方案 — {req['summary'][:50]}")
    return "\n".join(lines)


def get_request(request_id: str) -> str:
    """查看请求详情。"""
    req = _load_request(request_id)
    if req is None:
        return f"[error: 请求 {request_id} 不存在]"
    return json.dumps(req, ensure_ascii=False, indent=2)


# --- 工具 Schema ---

SHUTDOWN_REQ_TOOL = {
    "name": "shutdown_request",
    "description": "向队友发送安全关闭请求。队友完成当前工作后会响应。",
    "input_schema": {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "要关闭的队友名称"},
            "reason": {"type": "string", "description": "关闭原因"},
        },
        "required": ["target"],
    },
}

SHUTDOWN_RESP_TOOL = {
    "name": "shutdown_respond",
    "description": "响应关闭请求（队友使用）。批准后将安全退出。",
    "input_schema": {
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "关闭请求 ID"},
            "approve": {"type": "boolean", "description": "是否批准关闭"},
            "note": {"type": "string", "description": "备注说明"},
        },
        "required": ["request_id", "approve"],
    },
}

PLAN_REQ_TOOL = {
    "name": "plan_request",
    "description": "提交一个方案等待 Lead 审批（队友使用）。",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "方案摘要"},
            "details": {"type": "string", "description": "方案详细内容"},
        },
        "required": ["summary"],
    },
}

PLAN_REVIEW_TOOL = {
    "name": "plan_review",
    "description": "审批队友提交的方案。",
    "input_schema": {
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "方案请求 ID"},
            "approve": {"type": "boolean", "description": "是否批准"},
            "note": {"type": "string", "description": "审批意见"},
        },
        "required": ["request_id", "approve"],
    },
}

PROTOCOL_LIST_TOOL = {
    "name": "protocol_list",
    "description": "列出协议请求，可按状态和类型过滤。",
    "input_schema": {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "过滤状态：pending/approved/rejected"},
            "type": {"type": "string", "description": "过滤类型：shutdown/plan"},
        },
        "required": [],
    },
}

# Lead 专用工具（发起关闭、审批方案、查看列表）
LEAD_PROTOCOL_TOOLS = [SHUTDOWN_REQ_TOOL, PLAN_REVIEW_TOOL, PROTOCOL_LIST_TOOL]

# 队友专用工具（响应关闭、提交方案）
TEAMMATE_PROTOCOL_TOOLS = [SHUTDOWN_RESP_TOOL, PLAN_REQ_TOOL]


def make_lead_protocol_handlers():
    """创建 Lead Agent 的协议处理函数。"""
    return {
        "shutdown_request": lambda target, reason="": create_shutdown_request(target, reason),
        "plan_review": lambda request_id, approve, note="": review_plan(request_id, approve, note),
        "protocol_list": lambda status="", type="": list_requests(status, type),
    }


def make_teammate_protocol_handlers(teammate_name: str):
    """创建队友的协议处理函数。"""
    return {
        "shutdown_respond": lambda request_id, approve, note="": respond_shutdown(request_id, approve, note),
        "plan_request": lambda summary, details="": create_plan_request(teammate_name, summary, details),
    }
