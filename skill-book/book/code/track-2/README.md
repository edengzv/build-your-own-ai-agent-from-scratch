# Track 2: skill-creator 渐进演进

从 13 行到 599 行——一个 Skill 的完整进化史。

## 演进路线图

| 版本 | 对应章节 | 行数 | 新增技巧 |
|------|---------|------|---------|
| v01 | Ch1 基础 | 13 | 最小骨架 |
| v02 | Ch2 Description | 15 | What+When+Keywords 公式 |
| v03 | Ch3 指令 | 38 | 五要素 + Explain Why |
| v04 | Ch4 工作流 | 89 | 3-Pass 工作流 |
| v05 | Ch5 命令 | 134 | 命令路由表 |
| v06 | Ch6 示例 | 202 | I/O 示例 + 反例 |
| v07 | Ch7 架构 | 229 | 三层拆分 + scripts/ + reference/ |
| v08 | Ch8 工具 | 307 | Tool Usage 表 + Pipeline 编排 |
| v09 | Ch9 质量 | 321 | 10 项清单 + Guardrails + 反模式 |
| v10 | Ch10 测试 | 437 | Pass 4 评测 + 触发测试 + 断言 |
| v11 | Ch11 案例 | 506 | 复杂度路由 + 7 维审查 + 案例注入 |
| v12 | Ch12 元技能 | 599 | 生产级完整版 + 演化历程 |

## 如何阅读

每读完一章，查看对应版本的 diff：

```bash
# 看第 4 章（Multi-Pass）加了什么
diff v03-five-elements/SKILL.md v04-multi-pass/SKILL.md

# 看从最简到最终的完整演进
diff v01-basic/SKILL.md v12-final/SKILL.md
```

## 注意

- v01-v11 仅供学习，不建议直接用于生产
- 只有 **v12-final** 是生产级元技能
- v07 开始包含 scripts/ 和 reference/ 目录
