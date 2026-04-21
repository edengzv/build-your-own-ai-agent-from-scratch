# Skill 反模式参考

> 本文件供 Agent 在生成和审查 Skill 时通过 Read 工具查阅，用于识别和避免常见错误。

## 反模式列表

### 1. 万能 Skill（God Skill）

**症状**：description 过于宽泛，试图覆盖所有场景。

```yaml
# ✗ 差
description: 帮助用户处理所有代码相关的问题

# ✓ 好
description: >
  为 TypeScript 项目生成单元测试。当用户选中函数、打开测试文件、
  或要求写测试时使用。支持 Jest 和 Vitest 框架。
```

**修正**：收窄范围到一个具体任务。如果确实需要多个功能，用命令路由拆分。

---

### 2. 复读机（Parrot）

**症状**：大段复述用户输入而非处理。

```markdown
# ✗ 差
1. 用户说想要 X
2. 确认用户想要 X
3. 告诉用户我们将创建 X
4. 开始创建 X

# ✓ 好
1. 分析需求确定结构模式
2. 生成 SKILL.md
3. 验证输出质量
```

**修正**：删除复述步骤，直接进入处理逻辑。

---

### 3. 教科书型（Textbook）

**症状**：花大量 token 解释 Agent 已知的基础概念。

```markdown
# ✗ 差
## 什么是 YAML Frontmatter
YAML Frontmatter 是 Markdown 文件开头用 --- 包围的元数据区域...

# ✓ 好
（直接使用 YAML Frontmatter，不解释）
```

**修正**：删除所有解释性文字。如果是领域知识，放到 reference/ 按需查阅。

---

### 4. 模糊约束（Vague Constraint）

**症状**：使用"合适的"、"恰当的"、"必要时"等无法量化的表述。

```markdown
# ✗ 差
- 生成合适长度的 description
- 在必要时使用 Multi-Pass 模式

# ✓ 好
- description 长度 50-150 字，因为这是 Layer 1 的 token 预算
- 如果任务需要 3+ 步，使用 Multi-Pass 模式，因为分步更可控
```

**修正**：用具体数字、条件或规则替代模糊表述。

---

### 5. 工具遗漏（Tool Gap）

**症状**：指令中提到使用某工具，但 Tool Usage 表未列出。

```markdown
# ✗ 差 — 步骤中用了 Bash 但 Tool Usage 没写
## Tool Usage
| Tool | When | Purpose |
|------|------|---------|
| Read | Step 1 | 读取文件 |

## 执行步骤
1. Read 读取配置
2. 运行 `bash validate.sh`  ← Bash 未在表中声明

# ✓ 好 — Tool Usage 与步骤一致
## Tool Usage
| Tool | When | Purpose |
|------|------|---------|
| Read | Step 1 | 读取配置文件 |
| Bash | Step 2 | 运行验证脚本 |
```

**修正**：生成后检查 Tool Usage 表与指令中实际调用的工具是否一致。

---

### 6. 过度分层（Over-Architecture）

**症状**：< 80 行的简单 Skill 也搞三层架构。

```
# ✗ 差 — 一个 20 行的 quick-fix Skill 有 scripts/ 和 reference/
quick-fix/
├── SKILL.md (20 lines)
├── scripts/
│   └── validate.sh
└── reference/
    └── patterns.md

# ✓ 好 — 简单 Skill 保持单文件
quick-fix/
└── SKILL.md (20 lines)
```

**修正**：< 80 行保持单文件。只在确实有确定性逻辑或领域知识时才分层。

---

### 7. 欠触发（Under-Trigger）

**症状**：description 太简短或太技术化，导致 Agent 在该使用时未匹配到。

```yaml
# ✗ 差 — 只有 What，没有 When 和 Keywords
description: 生成 commit message

# ✓ 好 — What + When + Keywords
description: >
  Generate Conventional Commits messages from staged changes.
  Use after git add when the user wants a commit message,
  asks to commit, or needs to describe their changes.
```

**修正**：按 What+When+Keywords 三步法重写，确保覆盖用户可能的表述方式。

---

### 8. 无暂停交付（No-Pause Delivery）

**症状**：Multi-Pass Skill 在收集需求后直接生成，不让用户确认。

```markdown
# ✗ 差
### Pass 1
收集需求...
### Pass 2
直接生成...

# ✓ 好
### Pass 1
收集需求...
**暂停**：展示需求摘要，请用户确认后再继续。
### Pass 2
根据确认的需求生成...
```

**修正**：在关键决策点添加暂停，让用户有机会修正方向。

---

## 使用方法

生成 Skill 后，逐项比对以上反模式。如果命中任一项，按"修正"建议修改后重新检查。
