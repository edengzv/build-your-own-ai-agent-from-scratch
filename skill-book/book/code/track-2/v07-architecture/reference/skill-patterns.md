# Skill 设计模式参考

> 本文件供 Agent 在生成 Skill 时通过 Read 工具查阅，用于选择合适的结构模式。

## 模式一览

| 模式 | 适用场景 | 复杂度 | 典型行数 |
|------|---------|--------|---------|
| 单步模式 | 单一任务，输入→输出 | 低 | 10-50 |
| Multi-Pass 模式 | 需要收集→生成→验证 | 中 | 50-150 |
| 命令路由模式 | 多个独立子功能 | 中-高 | 100-200 |
| 三层架构模式 | 包含确定性逻辑+领域知识 | 高 | 150-300+ |

## 模式选择决策树

```
任务有几个独立子功能？
├── 1 个
│   ├── 需要几步？
│   │   ├── 1-2 步 → 单步模式
│   │   └── 3+ 步 → Multi-Pass 模式
│   └── 包含确定性逻辑？
│       ├── 是 → 三层架构模式
│       └── 否 → 保持当前模式
└── 2+ 个 → 命令路由模式
    └── 各子功能是否共享 Pass？
        ├── 是 → 命令路由 + 共享 Multi-Pass
        └── 否 → 命令路由 + 独立流程
```

## 单步模式

```markdown
## 执行步骤

1. 读取输入
2. 处理逻辑
3. 输出结果
```

适用于：quick-fix、commit-message 等简单任务。

## Multi-Pass 模式

```markdown
### Pass 1 — 信息收集
通过 AskUserQuestion 收集...
**暂停**：确认后继续。

### Pass 2 — 主逻辑
根据收集的信息...

### Pass 3 — 验证
检查输出质量...
```

关键原则：
- 每个 Pass 有明确的输入产物和输出产物
- Pass 之间用暂停点分隔
- 最后一个 Pass 是验证/审查

## 命令路由模式

```markdown
## Commands

| Command | Purpose |
|---------|---------|
| `/name verb1` | 功能描述 |
| `/name verb2` | 功能描述 |

默认行为：执行 `verb1`。

---

## `/name verb1`
...

## `/name verb2`
...
```

命名规范：
- 动词优先：`create`、`review`、`improve`
- 正交设计：每个命令做一件事，不重叠

## 三层架构模式

```
skill-name/
├── SKILL.md          # 路由层：指令 + 流程编排
├── scripts/          # 确定性逻辑：验证、计算、格式化
│   └── validate.sh   # stdout: JSON, stderr: status
└── reference/        # 知识文档：模式、清单、术语
    └── patterns.md   # Agent 用 Read 工具按需查阅
```

分层原则：
- **scripts/**：能确定性执行的 → 用脚本（不消耗上下文 token）
- **reference/**：需要理解和推理的 → 用文档（按需 Read）
- **SKILL.md**：串联流程 + 不属于以上两类的指令

脚本规范：
- shebang + `set -e`
- JSON 输出到 stdout
- 状态信息到 stderr
- 独立可运行（不依赖 SKILL.md 上下文）
