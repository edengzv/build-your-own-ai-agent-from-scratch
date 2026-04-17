"""
MiniAgent — Skill Loader
按需加载领域知识的两层注入系统。

Layer 1: 扫描 skills 目录，将 name + description 注入 system prompt (~100 tokens each)
Layer 2: Agent 调用 load_skill 工具时，读取完整 SKILL.md 内容
"""

import os
import re

SKILLS_DIR = os.path.join(os.getcwd(), "skills")


def _parse_frontmatter(content: str) -> dict:
    """解析 SKILL.md 的 YAML frontmatter。"""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}
    meta = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def scan_skills() -> list[dict]:
    """扫描 skills 目录，返回 [{name, description, path}]。"""
    skills = []
    if not os.path.isdir(SKILLS_DIR):
        return skills

    for entry in sorted(os.listdir(SKILLS_DIR)):
        skill_md = os.path.join(SKILLS_DIR, entry, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()
            meta = _parse_frontmatter(content)
            name = meta.get("name", entry)
            desc = meta.get("description", "No description")
            skills.append({"name": name, "description": desc, "path": skill_md})
        except Exception:
            continue
    return skills


def build_skill_summary(skills: list[dict]) -> str:
    """构建注入到 system prompt 的 skill 摘要。"""
    if not skills:
        return ""
    lines = ["\n可用的知识技能（用 load_skill 工具按需加载）:"]
    for s in skills:
        lines.append(f"  - {s['name']}: {s['description'][:100]}")
    return "\n".join(lines)


def load_skill_content(skill_name: str, skills: list[dict]) -> str:
    """加载指定 skill 的完整 SKILL.md 内容。"""
    for s in skills:
        if s["name"] == skill_name:
            try:
                with open(s["path"], "r", encoding="utf-8") as f:
                    content = f.read()
                # 去掉 frontmatter，只返回正文
                cleaned = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)
                return f"[Skill: {skill_name}]\n{cleaned.strip()}"
            except Exception as e:
                return f"[error: 无法读取 skill '{skill_name}': {e}]"
    available = ", ".join(s["name"] for s in skills)
    return f"[error: 未找到 skill '{skill_name}'。可用: {available or '无'}]"


# --- 工具 Schema ---
LOAD_SKILL_TOOL = {
    "name": "load_skill",
    "description": (
        "按名称加载一个知识技能的完整内容。"
        "系统提示中列出了可用的技能名称和简介，用此工具获取详细内容。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "要加载的技能名称",
            }
        },
        "required": ["name"],
    },
}


def make_load_skill_handler(skills: list[dict]):
    """创建绑定到 skills 列表的 handler。"""

    def handle_load_skill(name: str) -> str:
        return load_skill_content(name, skills)

    return handle_load_skill
