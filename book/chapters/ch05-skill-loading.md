# Chapter 5: 知识加载

> **Motto**: "需要的时候再加载知识，而不是一开始就塞满"

> 你的 Agent 现在能规划任务、操作文件、记住对话。但它仍然只有"通用知识"——它不知道你的团队用什么代码风格，不知道你的项目有什么约定，也不知道如何按照特定规范做代码审查。本章你将构建一个 Skill（技能）系统，让 Agent 能按需加载领域知识，从"什么都会一点"变为"需要时能精通"。

## The Problem

假设你希望 Agent 按照团队规范做代码审查。最直觉的做法是把审查指南塞进 system prompt：

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

这有三个问题：

1. **上下文浪费**：每次对话都带着 5000+ 字的规范，哪怕用户只是问"几点了"。这些 token 占用了宝贵的上下文空间——第 6 章你会深刻理解这一点。

2. **注意力稀释**：LLM 的注意力不是均匀分布的。system prompt 越长，模型对其中任何一段的注意力越低。把审查指南和 API 规范混在一起，两边的执行质量都会下降。

3. **无法扩展**：一个能做 20 种不同任务的 Agent，总不能把 20 份指南全塞进去。

我们需要一种"按需加载"的机制：Agent 知道有哪些知识可用，需要时再去获取。

## The Solution

借鉴操作系统的虚拟内存思想——"不是所有数据都需要在内存中，需要时再从磁盘加载"——我们设计一个两层注入系统：

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

**Layer 1 — 目录注入**：启动时扫描 `skills/` 目录，读取每个技能的名称和简介（从 YAML frontmatter 提取），拼接到 system prompt 末尾。每个技能只占约 100 tokens。

**Layer 2 — 按需加载**：提供 `load_skill` 工具。Agent 根据 Layer 1 的摘要判断当前任务是否需要某个技能，如果需要，主动调用工具加载完整内容。完整内容作为 tool_result 进入对话历史。

这个设计的关键洞察是：**让 Agent 自己决定何时需要什么知识**。我们不需要写复杂的路由逻辑，只需要给它一个目录和一把钥匙。

## 5.1 Skill 目录结构

每个 Skill 是一个目录，核心是一个 `SKILL.md` 文件：

```
miniagent/
├── agent.py
├── todo.py
├── skill_loader.py      ← NEW
└── skills/              ← NEW
    └── code-review/
        └── SKILL.md
```

`SKILL.md` 使用 YAML frontmatter 声明元数据，正文是 Markdown 格式的指令：

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

为什么用 YAML frontmatter？因为它把"给机器读的"（name, description）和"给 Agent 读的"（正文指令）清晰分开。Layer 1 只需要解析 frontmatter；Layer 2 返回正文。

> **设计原则**：`description` 字段至关重要。它是 Agent 在 system prompt 中唯一看到的信息，必须准确描述技能的用途。好的 description 让 Agent 在正确的时机加载正确的技能；坏的 description 要么让 Agent 忽略有用的技能，要么频繁加载不需要的技能。

## 5.2 实现 skill_loader.py

创建 `skill_loader.py` —— 整个 Skill 系统的实现只需要 100 行代码：

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

首先解析 frontmatter。不需要引入 YAML 库——我们的格式简单到手写解析就够了：

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

然后是 Layer 1 的扫描和摘要生成：

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

注意 `build_skill_summary` 截断了 description 的长度——这确保 Layer 1 不会因为某个过长的描述而膨胀。

Layer 2 的按需加载：

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

返回内容时去掉 frontmatter 是因为 Agent 不需要看到 name 和 description——它已经知道了。正文才是有价值的指令。

最后是工具 schema 和工厂函数：

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

这里再次用了第 4 章引入的**工厂函数模式**——`make_load_skill_handler` 将 `skills` 列表"封装"进闭包，避免全局变量。

## 5.3 集成到 Agent

现在把 Skill 系统接入 `agent.py`。改动集中在五处：

**1. 导入和初始化**（文件顶部）：

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

在模块加载时就完成扫描——这意味着添加新 Skill 后需要重启 Agent。对于学习项目来说这是合理的简化。

**2. 更新 system prompt**：

```python
SYSTEM_TEMPLATE = """你是 MiniAgent，一个通用 AI 助手。

...
- 需要领域知识时，用 load_skill 加载对应技能
...
""" + _skill_summary  # CHANGED: 动态追加 skill 摘要
```

`_skill_summary` 会生成类似这样的内容追加到 system prompt 末尾：

```
可用的知识技能（用 load_skill 工具按需加载）:
  - code-review: 审查代码质量，检查常见问题，提供改进建议
```

**3. 注册工具 schema**：

```python
TOOLS = [
    # ... 已有的 bash, read_file, write_file, edit_file ...
    TODO_TOOL,
    LOAD_SKILL_TOOL,  # NEW
]
```

**4. 注册 handler**（在 `agent_loop` 内部）：

```python
handlers = {
    # ... 已有的 bash, read_file, write_file, edit_file ...
    "load_skill": make_load_skill_handler(_skills),  # NEW
}
```

**5. 更新 REPL 显示**：

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

现在启动 REPL 时，你会看到已识别的技能列表。

## 5.4 试一试

确保项目结构正确：

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

启动 Agent：

```bash
cd miniagent
python agent.py
```

你应该看到：

```
MiniAgent REPL (输入 'exit' 退出, 'clear' 清空对话)
工作目录: /path/to/miniagent
工具: bash, read_file, write_file, edit_file, todo, load_skill
技能: code-review
--------------------------------------------------
```

试试让 Agent 做代码审查：

```
You: 帮我审查一下 agent.py 的代码质量
```

观察 Agent 的行为——它应该会：

1. 先用 `read_file` 读取 `agent.py`
2. 识别到这是代码审查任务，调用 `load_skill("code-review")` 加载审查指南
3. 按照指南的清单逐项审查
4. 输出格式化的审查报告

如果 Agent 没有加载技能就直接审查，那也是正确的——它可能觉得自己内置的知识足够。关键是它**知道有这个选项**，并且在需要时能够使用。

> **Try It Yourself**：创建一个新的 Skill。比如一个 `python-style` 技能，在 `skills/python-style/SKILL.md` 中定义你团队的 Python 编码规范。然后让 Agent 用你的规范检查一段代码。

## 5.5 设计好的 Skill

Skill 系统的效果取决于 Skill 本身的质量。以下是一些设计原则：

**1. description 是最关键的一行**

Agent 根据 description 决定何时加载。好的 description：

```yaml
description: 审查代码质量，检查常见问题（安全、性能、可读性），提供改进建议
```

坏的 description：

```yaml
description: 代码相关的技能
```

太模糊，Agent 不知道什么时候该用它。

**2. 指令要具体、可执行**

Skill 正文应该是可以直接"照做"的指令，而非抽象的原则。

好的：
```markdown
## 输出格式
对每个问题使用以下格式：
[severity: high/medium/low]
文件: <path>
问题: <description>
建议: <suggestion>
```

坏的：
```markdown
审查代码时注意各种问题，给出适当的建议。
```

**3. 保持单一职责**

一个 Skill 做一件事。不要把"代码审查"和"API 设计"混在一个 Skill 里。让 Agent 按需组合比让 Skill 面面俱到要好。

**4. 控制篇幅**

理想的 Skill 在 500-2000 tokens（约 300-1200 中文字）。过短没有价值，过长会在加载后挤占上下文空间——第 6 章的上下文管理会进一步讨论这个问题。

## What Changed

```
miniagent/
├── agent.py            ← CHANGED: +20 行（skill 导入、初始化、handler、REPL 显示）
├── todo.py
├── skill_loader.py     ← NEW: 103 行（扫描、摘要、加载、工具定义）
├── requirements.txt
└── skills/             ← NEW: 技能目录
    └── code-review/
        └── SKILL.md    ← NEW: 示例技能
```

| 指标 | Chapter 4 | Chapter 5 |
|------|-----------|-----------|
| 工具数 | 5 | **6** (+load_skill) |
| 模块数 | 2 | **3** (+skill_loader.py) |
| 能力 | 规划任务 | **+按需加载领域知识** |
| 知识来源 | 仅模型内置 | **模型内置 + 外部 Skill 文件** |

**核心架构演进**：

```
Ch1-3: Agent = Model + 工具
Ch4:   Agent = Model + 工具 + 规划
Ch5:   Agent = Model + 工具 + 规划 + 知识     ← you are here
```

Agent 的 Harness 又丰富了一层。我们在第 1 章说过 Agent = Model + Harness，现在你看到 Harness 是如何一步步丰满起来的。

## Summary

- 把所有知识塞进 system prompt 浪费上下文、稀释注意力、无法扩展
- 两层注入架构解决了这个问题：Layer 1 轻量目录（system prompt），Layer 2 按需加载（tool call）
- `SKILL.md` 的 `description` 字段决定了 Agent 何时加载——精心编写它
- 工厂函数模式再次出现——`make_load_skill_handler` 封装状态到闭包
- Skill 设计原则：精准 description、具体指令、单一职责、控制篇幅

下一章，我们将面对一个更根本的挑战：上下文窗口终会溢出。当 Agent 执行了太多工具调用、读了太多文件后，消息列表会超出模型的处理能力。你需要一种"腾出空间"的方法。
