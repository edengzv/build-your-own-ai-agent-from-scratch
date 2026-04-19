<!-- Translated from: ch05-skill-loading.md -->

# Chapter 5: Skill Loading

> **Motto**: "Load knowledge when you need it, not all at once from the start."

> Your agent can now plan tasks, manipulate files, and remember conversations. But it still only has "general knowledge" -- it does not know your team's coding style, your project's conventions, or how to perform a code review according to a specific standard. In this chapter you build a Skill system that lets the agent load domain knowledge on demand, transforming it from "knows a little about everything" to "expert when it needs to be."

![Conceptual: Pluggable knowledge modules](images/ch05/fig-05-01-concept.png)

*Figure 5-1. Error recovery: when the path breaks, build a bridge and keep moving.*
## The Problem

Say you want the agent to do code reviews following your team's guidelines. The most intuitive approach is to stuff the review guide into the system prompt:

```python
SYSTEM_TEMPLATE = """你是 MiniAgent，一个通用 AI 助手。

你的能力：
- 执行 bash 命令
- 读取、写入、编辑文件
- 管理任务列表

## 代码审查指南

### 1. 正确性检查
检查逻辑错误、边界条件、空值处理...
（500 字）

### 2. 安全性检查
检查注入攻击、路径遍历、信息泄露...
（500 字）

### 3. 性能检查
检查 N+1 查询、不必要的循环...
（500 字）

### 4. 可读性检查
检查命名规范、函数长度...
（500 字）

... 还有 UI 设计规范、API 文档规范、测试编写规范 ...
"""
```

This has three problems:

1. **Wasted context**: Every conversation carries 5,000+ words of guidelines, even if the user just asks "what time is it?" Those tokens eat into precious context space -- you will feel this acutely in Chapter 6.

2. **Diluted attention**: LLM attention is not distributed evenly. The longer the system prompt, the less attention the model pays to any given part of it. Mix review guidelines with API specs and the execution quality of both degrades.

3. **Cannot scale**: An agent that handles 20 different tasks cannot stuff 20 different guides into the prompt.

We need a "load on demand" mechanism: the agent knows what knowledge is available and fetches it when needed.

## The Solution

Borrowing from the virtual memory concept in operating systems -- "not all data needs to be in memory; load from disk when needed" -- we design a two-layer injection system:

```
┌──────────────────────────────────────────┐
│              System Prompt               │
│                                          │
│  "你是 MiniAgent..."                     │
│  "你的能力: ..."                         │
│                                          │
│  可用技能（Layer 1 ≈ 100 tokens each）:  │
│   - code-review: 审查代码质量            │
│   - api-design: API 设计规范             │
│   - test-writing: 测试编写指南           │
│                                          │
└──────────────────┬───────────────────────┘
                   │
                   │ Agent 决定需要某个技能
                   ↓
          ┌──────────────┐
          │ load_skill() │  ← Layer 2: 按需加载完整内容
          └──────┬───────┘
                 ↓
    ┌────────────────────────┐
    │  skills/code-review/   │
    │    SKILL.md (完整内容)  │
    │    ~2000 tokens        │
    └────────────────────────┘
```

**Layer 1 -- Catalog injection**: At startup, scan the `skills/` directory, read each skill's name and description (extracted from YAML frontmatter), and append them to the end of the system prompt. Each skill costs only about 100 tokens.

**Layer 2 -- On-demand loading**: Provide a `load_skill` tool. The agent uses the Layer 1 summaries to judge whether the current task needs a particular skill, and if so, proactively calls the tool to load the full content. That content enters the conversation history as a tool_result.

The key insight behind this design is: **let the agent itself decide when it needs what knowledge**. We do not need to write complex routing logic -- just give it a catalog and a key.

## 5.1 Skill Directory Structure

Each Skill is a directory whose core is a `SKILL.md` file:

```
miniagent/
├── agent.py
├── todo.py
├── skill_loader.py      ← NEW
└── skills/              ← NEW
    └── code-review/
        └── SKILL.md
```

`SKILL.md` uses YAML frontmatter for metadata, with the body in Markdown as instructions:

```markdown
---
name: code-review
description: 审查代码质量，检查常见问题，提供改进建议
---

# Code Review Skill

你是一个代码审查专家。当用户请求代码审查时，按以下步骤操作：

## 审查清单

1. **正确性**: 逻辑是否正确？边界条件是否处理？
2. **安全性**: 是否有注入、路径遍历、信息泄露等风险？
3. **可读性**: 命名是否清晰？结构是否合理？
...
```

Why YAML frontmatter? Because it cleanly separates "machine-readable" data (name, description) from "agent-readable" data (the instruction body). Layer 1 only needs to parse the frontmatter; Layer 2 returns the body.

> **Design Principle**: The `description` field is critically important. It is the only information the agent sees in the system prompt, so it must accurately describe the skill's purpose. A good description makes the agent load the right skill at the right time; a bad description causes the agent to either ignore useful skills or load unnecessary ones too often.

## 5.2 Implementing skill_loader.py

Create `skill_loader.py` -- the entire Skill system fits in about 100 lines of code:

```python
"""
MiniAgent — Skill Loader
按需加载领域知识的两层注入系统。

Layer 1: 扫描 skills 目录，将 name + description 注入 system prompt
Layer 2: Agent 调用 load_skill 工具时，读取完整 SKILL.md 内容
"""

import os
import re

SKILLS_DIR = os.path.join(os.getcwd(), "skills")
```

First, parse the frontmatter. No need to pull in a YAML library -- our format is simple enough to parse by hand:

```python
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
```

Next, the Layer 1 scan and summary generation:

```python
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
```

Notice that `build_skill_summary` truncates the description length -- this ensures Layer 1 does not bloat because of one overly long description.

Layer 2, the on-demand loading:

```python
def load_skill_content(skill_name: str, skills: list[dict]) -> str:
    """加载指定 skill 的完整 SKILL.md 内容。"""
    for s in skills:
        if s["name"] == skill_name:
            try:
                with open(s["path"], "r", encoding="utf-8") as f:
                    content = f.read()
                # 去掉 frontmatter，只返回正文
                cleaned = re.sub(
                    r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL
                )
                return f"[Skill: {skill_name}]\n{cleaned.strip()}"
            except Exception as e:
                return f"[error: 无法读取 skill '{skill_name}': {e}]"
    available = ", ".join(s["name"] for s in skills)
    return f"[error: 未找到 skill '{skill_name}'。可用: {available or '无'}]"
```

The frontmatter is stripped from the returned content because the agent does not need to see the name and description again -- it already knows those. The body is what carries the valuable instructions.

Finally, the tool schema and factory function:

```python
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
```

Here we use the **factory function pattern** introduced in Chapter 4 once again -- `make_load_skill_handler` "captures" the `skills` list inside a closure, avoiding global variables.

## 5.3 Integrating with the Agent

Now wire the Skill system into `agent.py`. The changes touch five places:

**1. Import and initialization** (top of file):

```python
from skill_loader import (  # NEW
    scan_skills,
    build_skill_summary,
    LOAD_SKILL_TOOL,
    make_load_skill_handler,
)

# NEW: Skill 系统初始化
_skills = scan_skills()
_skill_summary = build_skill_summary(_skills)
```

The scan happens at module load time -- this means you need to restart the agent after adding a new Skill. For a learning project, that is a reasonable simplification.

**2. Update the system prompt**:

```python
SYSTEM_TEMPLATE = """你是 MiniAgent，一个通用 AI 助手。

...
- 需要领域知识时，用 load_skill 加载对应技能
...
""" + _skill_summary  # CHANGED: 动态追加 skill 摘要
```

`_skill_summary` generates something like this, appended to the end of the system prompt:

```
可用的知识技能（用 load_skill 工具按需加载）:
  - code-review: 审查代码质量，检查常见问题，提供改进建议
```

**3. Register the tool schema**:

```python
TOOLS = [
    # ... 已有的 bash, read_file, write_file, edit_file ...
    TODO_TOOL,
    LOAD_SKILL_TOOL,  # NEW
]
```

**4. Register the handler** (inside `agent_loop`):

```python
handlers = {
    # ... 已有的 bash, read_file, write_file, edit_file ...
    "load_skill": make_load_skill_handler(_skills),  # NEW
}
```

**5. Update the REPL display**:

```python
def repl():
    """交互式对话循环。"""
    messages = []
    todo_manager = TodoManager()
    print("MiniAgent REPL (输入 'exit' 退出, 'clear' 清空对话)")
    print(f"工作目录: {WORKSPACE}")
    tool_names = [t["name"] for t in TOOLS]
    print(f"工具: {', '.join(tool_names)}")  # CHANGED: 动态列出所有工具
    if _skills:  # NEW: 显示已加载的技能
        print(f"技能: {', '.join(s['name'] for s in _skills)}")
    else:
        print("技能: (未找到 skills/ 目录)")
    print("-" * 50)
```

Now when you start the REPL, you see the list of recognized skills.

## 5.4 Try It Out

Make sure the project structure is correct:

```bash
miniagent/
├── agent.py
├── todo.py
├── skill_loader.py
├── requirements.txt
└── skills/
    └── code-review/
        └── SKILL.md
```

Start the agent:

```bash
cd miniagent
python agent.py
```

You should see:

```
MiniAgent REPL (输入 'exit' 退出, 'clear' 清空对话)
工作目录: /path/to/miniagent
工具: bash, read_file, write_file, edit_file, todo, load_skill
技能: code-review
--------------------------------------------------
```

Try asking the agent to do a code review:

```
You: 帮我审查一下 agent.py 的代码质量
```

Watch the agent's behavior -- it should:

1. Use `read_file` to read `agent.py`
2. Recognize this is a code review task and call `load_skill("code-review")` to load the review guidelines
3. Walk through the checklist item by item
4. Output a formatted review report

If the agent reviews without loading the skill, that is also fine -- it may have decided its built-in knowledge was sufficient. The point is that it **knows the option exists** and can use it when needed.

> **Try It Yourself**: Create a new Skill. For example, a `python-style` skill in `skills/python-style/SKILL.md` that defines your team's Python coding conventions. Then ask the agent to check a piece of code against your conventions.

## 5.5 Designing Good Skills

The effectiveness of the Skill system depends on the quality of the Skills themselves. Here are some design principles:

**1. The description is the single most critical line**

The agent decides when to load a skill based on the description. A good description:

```yaml
description: 审查代码质量，检查常见问题（安全、性能、可读性），提供改进建议
```

A bad description:

```yaml
description: 代码相关的技能
```

Too vague -- the agent has no idea when to use it.

**2. Instructions should be specific and actionable**

The body of a Skill should contain instructions the agent can follow directly, not abstract principles.

Good:
```markdown
## 输出格式
对每个问题使用以下格式：
[severity: high/medium/low]
文件: <path>
问题: <description>
建议: <suggestion>
```

Bad:
```markdown
审查代码时注意各种问题，给出适当的建议。
```

**3. Keep to a single responsibility**

One Skill does one thing. Do not mix "code review" and "API design" in the same Skill. Letting the agent combine skills on demand is better than making one skill try to cover everything.

**4. Control the length**

The ideal Skill is 500-2,000 tokens (roughly 300-1,200 Chinese characters). Too short and it adds no value; too long and it crowds out context space after loading -- Chapter 6's context management digs deeper into this.

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +20 行（skill 导入、初始化、handler、REPL 显示）
├── todo.py
├── skill_loader.py     ← NEW: 102 行（扫描、摘要、加载、工具定义）
├── requirements.txt
└── skills/             ← NEW: 技能目录
    └── code-review/
        └── SKILL.md    ← NEW: 示例技能
```

| Metric | Chapter 4 | Chapter 5 |
|--------|-----------|-----------|
| Tools | 5 | **6** (+load_skill) |
| Modules | 2 | **3** (+skill_loader.py) |
| Capability | Task planning | **+ On-demand domain knowledge** |
| Knowledge source | Model built-in only | **Model built-in + external Skill files** |

**Core architecture evolution**:

```
Ch1-3: Agent = Model + 工具
Ch4:   Agent = Model + 工具 + 规划
Ch5:   Agent = Model + 工具 + 规划 + 知识     ← you are here
```

The agent's Harness has grown another layer. Back in Chapter 1 we said Agent = Model + Harness -- now you can see how the Harness fills out step by step.

## Summary

- Stuffing all knowledge into the system prompt wastes context, dilutes attention, and cannot scale
- A two-layer injection architecture solves this: Layer 1 is a lightweight catalog (system prompt), Layer 2 is on-demand loading (tool call)
- The `description` field of `SKILL.md` determines when the agent loads a skill -- write it with care
- The factory function pattern appears again -- `make_load_skill_handler` captures state in a closure
- Skill design principles: precise description, specific instructions, single responsibility, controlled length

In the next chapter, we face a more fundamental challenge: the context window will eventually overflow. After the agent has made too many tool calls and read too many files, the message list exceeds the model's capacity. You need a way to "free up space."
