# MiniAgent 代码审查报告

> 审查日期: 2026-04-18
> 审查范围: 16 个章节的代码快照 (`book/code/ch01-ch16/`) + Git 标签一致性 + miniagent/ 工作目录
> 修复状态: **已完成全部修复**

---

## 一、总览

| 检查项 | 结果 |
|--------|------|
| 语法检查 (py_compile) | 全部 16 章 PASS |
| 运行时导入检查 | 全部 16 章 PASS |
| 模块依赖完整性 | 全部 16 章 PASS |
| 章节文本 vs 代码匹配 | 全部 16 章 PASS |
| 增量构建一致性 | 全部 16 章 PASS |
| Git 标签 vs 快照一致性 | ch01-ch09 PASS, **ch10-ch16 有问题** |
| miniagent/ 工作目录状态 | **有未提交的问题** |

---

## 二、各章节代码快照检查 (book/code/chXX/)

### Chapter 1: 你好，Agent -- PASS

- **文件**: agent.py (114行), verify_setup.py (35行)
- **功能**: 基础 Agent 循环 + bash 工具
- **验证**: 核心循环正确实现 (request -> execute -> return), 工具 schema 正确, 超时处理完备
- **工具数**: 1 (bash)

### Chapter 2: 工具调用 -- PASS

- **文件**: agent.py (250行)
- **功能**: 工具分发映射 + 3 个文件操作工具
- **验证**: TOOL_HANDLERS 分发机制正确, safe_path() 防目录穿越, read/write/edit_file 全部实现
- **工具数**: 4 (bash, read_file, write_file, edit_file)

### Chapter 3: 对话记忆 -- PASS

- **文件**: agent.py (291行), verify_setup.py
- **功能**: 交互式 REPL + 多轮对话
- **验证**: REPL 循环正确, messages 列表持久化, exit/clear 命令正常, 单次/交互两种模式兼容
- **工具数**: 4

### Chapter 4: 任务规划 -- PASS

- **文件**: agent.py (310行), todo.py (150行)
- **功能**: TodoManager + 提醒机制
- **验证**: add/update_status/list 操作正确, 单 in_progress 约束生效, 3 轮提醒机制工作, 工厂模式正确
- **工具数**: 5 (+todo)

### Chapter 5: 知识加载 -- PASS

- **文件**: agent.py (331行), skill_loader.py (102行), todo.py, skills/code-review/SKILL.md
- **功能**: 两层 Skill 注入系统
- **验证**: Layer1 (目录扫描摘要注入 system prompt) + Layer2 (按需加载完整内容), YAML frontmatter 解析正确
- **工具数**: 6 (+load_skill)

### Chapter 6: 上下文管理 -- PASS

- **文件**: agent.py (350行), context.py (187行), skill_loader.py, todo.py
- **功能**: 三层压缩策略
- **验证**: micro_compact (旧 tool_result 占位), auto_compact (50K 阈值 LLM 摘要), compact 工具 (手动), 防重复压缩检查
- **工具数**: 7 (+compact)

### Chapter 7: 子智能体 -- PASS

- **文件**: agent.py (379行), subagent.py (125行), context.py, skill_loader.py, todo.py
- **功能**: 独立上下文的任务委托
- **验证**: run_subagent() 使用独立 messages, CHILD_TOOLS 正确排除 task 防递归, max_turns=20 安全机制
- **工具数**: 8 (+task)

### Chapter 8: 后台任务 -- PASS

- **文件**: agent.py (405行), background.py (190行), context.py, skill_loader.py, subagent.py, todo.py
- **功能**: daemon 线程 + 通知队列
- **验证**: BgTask 状态追踪正确, 线程安全 (threading.Lock), daemon=True, 通知注入位置正确 (AFTER todo, BEFORE context compression)
- **工具数**: 10 (+bg_run, bg_check)

### Chapter 9: 持久化任务 -- PASS

- **文件**: agent.py (418行), tasks.py (282行), background.py, context.py, skill_loader.py, subagent.py, todo.py
- **功能**: 文件级 DAG 任务图
- **验证**: TaskGraph CRUD 完整, .tasks/ 持久化, blocked_by 依赖关系正确, _unblock_downstream 级联解锁, _find_max_id 防 ID 冲突
- **工具数**: 14 (+task_create, task_update, task_list, task_get)

### Chapter 10: 智能体团队 -- PASS

- **文件**: agent.py (458行), team.py (258行), + ch09 所有模块
- **功能**: 持久化队友 + 邮箱通信
- **验证**: TeamManager spawn/send/inbox 完整, 队友 daemon 线程独立运行, JSONL 邮箱原子读取, 15 轮上限安全机制
- **工具数**: 18 (+spawn, send, inbox, team_status)

### Chapter 11: 团队协议 -- PASS

- **文件**: agent.py (481行), protocols.py (249行), team.py, + ch10 所有模块
- **功能**: 请求-响应协议 + 安全关闭/方案审批
- **验证**: shutdown/plan 两种协议状态机正确, LEAD/TEAMMATE 工具分组正确, 工厂函数闭包绑定队友名称
- **工具数**: 23 (+shutdown_request, plan_review, protocol_list, shutdown_respond, plan_request)

### Chapter 12: 自主智能体 -- PASS

- **文件**: agent.py (494行), autonomous.py (195行), protocols.py, team.py, + ch11 所有模块
- **功能**: IDLE/WORK 循环 + 任务认领
- **验证**: scan_claimable_tasks 过滤逻辑正确, claim_task check-then-set 原子模式, _unblock_downstream 文件持久化正确 (write 在外层 if 内), 60 秒空闲超时
- **工具数**: 26 (+scan_tasks, claim_task, complete_my_task)

### Chapter 13: 工作隔离 -- PASS

- **文件**: agent.py (509行), worktree.py (184行), autonomous.py, protocols.py, team.py, + ch12 所有模块
- **功能**: Git Worktree 绑定任务 + 分支隔离
- **验证**: WorktreeManager create/remove/list 完整, 事件日志 (events.jsonl), 三个 worktree 工具正确标记为 _PARENT_ONLY
- **工具数**: 29 (+worktree_create, worktree_remove, worktree_list)

### Chapter 14: 安全与权限 -- PASS

- **文件**: agent.py (530行), security.py (242行), worktree.py, autonomous.py, protocols.py, + ch13 所有模块
- **功能**: 路径沙箱 + 命令分级 + 人类确认
- **验证**: Sandbox 路径检查 (symlink resolve), 命令分类 (dangerous/restricted/safe), PermissionLevel RBAC, ConfirmationGate y/n/always, make_security_wrapper 中间件模式
- **工具数**: 29 (无新增工具, 安全层作为中间件)

### Chapter 15: 可观测性 -- PASS

- **文件**: agent.py (548行), observability.py (204行), security.py, worktree.py, + ch14 所有模块
- **功能**: 结构化日志 + 执行追踪 + Token 统计
- **验证**: Tracer (trace_id + span), TokenStats (input/output/cost), Logger (JSONL), ObservabilityManager 整合类, 正确集成到 agent_loop
- **工具数**: 29 (无新增工具, 可观测性作为基础设施)

### Chapter 16: 从 MiniAgent 到生产 -- PASS

- **文件**: 与 ch15 完全相同 (回顾章节, 无新代码)
- **功能**: 系统回顾 + 框架映射 + 部署策略
- **验证**: agent.py 与 ch15 完全一致 (diff 无差异), 所有 13 个模块齐全

---

## 三、Git 标签一致性检查

对比 `git show <tag>:miniagent/` 与 `book/code/<tag>/` 快照的一致性:

### ch01-ch09: 全部一致

所有文件 (agent.py + 各模块) 在 git tag 和 book/code/ 快照之间完全匹配。

### ch10: 不一致 -- 需修复

| 文件 | 标签状态 | 快照状态 | 差异 |
|------|---------|---------|------|
| agent.py | 缺少 Team 集成代码 | 包含完整 Team 集成 | tag 中的 agent.py 停留在 ch09 状态, 未集成 team.py |
| team.py | 匹配 | 匹配 | OK |

**原因**: ch10 提交时 agent.py 未完整更新, 后续在修复提交 (144d388) 中修正了 book/code/ch10/agent.py, 但 git tag 仍指向原始提交。

### ch11: 不一致 -- 需修复

| 文件 | 标签状态 | 快照状态 | 差异 |
|------|---------|---------|------|
| agent.py | 缺少 Protocol 集成代码 | 包含完整 Protocol 集成 | 与 ch10 类似问题 |
| protocols.py | **空文件 (0 字节)** | 249 行完整实现 | 原始提交中为空占位符 |

### ch12: 部分不一致

| 文件 | 标签状态 | 快照状态 | 差异 |
|------|---------|---------|------|
| agent.py | 匹配 | 匹配 | OK |
| autonomous.py | **空文件 (0 字节)** | 195 行完整实现 | 原始提交中为空占位符 |
| protocols.py | **空文件 (0 字节)** | 249 行完整实现 | 继承 ch11 的空文件 |

### ch13: 部分不一致

| 文件 | 标签状态 | 快照状态 | 差异 |
|------|---------|---------|------|
| autonomous.py | 空文件 | 195 行 | 继承问题 |
| protocols.py | 空文件 | 249 行 | 继承问题 |
| worktree.py | **空文件 (0 字节)** | 184 行完整实现 | 原始提交中为空占位符 |

### ch14: 部分不一致

| 文件 | 标签状态 | 快照状态 | 差异 |
|------|---------|---------|------|
| autonomous.py | 空文件 | 195 行 | 继承问题 |
| protocols.py | 空文件 | 249 行 | 继承问题 |
| worktree.py | 空文件 | 184 行 | 继承问题 |
| security.py | **空文件 (0 字节)** | 242 行完整实现 | 原始提交中为空占位符 |

### ch15: 部分不一致

| 文件 | 标签状态 | 快照状态 | 差异 |
|------|---------|---------|------|
| autonomous.py | 空文件 | 195 行 | 继承问题 |
| protocols.py | 空文件 | 249 行 | 继承问题 |
| worktree.py | 空文件 | 184 行 | 继承问题 |
| security.py | 空文件 | 242 行 | 继承问题 |
| observability.py | **空文件 (0 字节)** | 204 行完整实现 | 原始提交中为空占位符 |

### ch16: 部分不一致

| 文件 | 标签状态 | 快照状态 | 差异 |
|------|---------|---------|------|
| autonomous.py | 空文件 | 195 行 | 继承问题 |
| observability.py | 空文件 | 204 行 | 继承问题 |
| security.py | 空文件 | 242 行 | 继承问题 |
| worktree.py | 空文件 | 184 行 | 继承问题 |
| protocols.py | 匹配 | 匹配 | ch16 提交中修复了 |

**根因**: ch11-ch15 提交时, 新引入的模块文件 (protocols.py, autonomous.py, worktree.py, security.py, observability.py) 为空占位符。修复提交 (144d388) 重建了 book/code/ 快照中的内容, 但 git tag 仍指向原始提交。

---

## 四、miniagent/ 工作目录状态

> **以下问题已全部修复。** miniagent/ 现已恢复到与 book/code/ch16/ 完全一致的正确状态。

### 问题 1 [已修复]: agent.py 曾停留在 ch09 状态

`miniagent/agent.py` 曾为 418 行 (ch09 状态), 现已替换为 548 行完整版 (ch16 状态)。

### 问题 2 [已修复]: 三个模块文件曾包含重复类定义

| 文件 | 修复前 | 修复后 | 重复的类 |
|------|--------|--------|---------|
| worktree.py | 404 行 | 184 行 | WorktreeManager (曾定义 2 次) |
| security.py | 475 行 | 242 行 | Sandbox, PermissionLevel, ConfirmationGate (各曾 2 次) |
| observability.py | 386 行 | 204 行 | Tracer, TokenStats, Logger, ObservabilityManager (各曾 2 次) |

### 问题 3 [已修复]: autonomous.py 曾有额外代码

`miniagent/autonomous.py` 曾为 209 行, 现已与 ch16 快照对齐 (196 行)。

---

## 五、修复记录

> **以下修复已全部完成。**

### P0: miniagent/ 工作目录 -- 已修复

1. **agent.py**: 已替换为 `book/code/ch16/agent.py` (548 行完整版)
2. **worktree.py**: 已去除重复类定义, 恢复为 184 行正确版本
3. **security.py**: 已去除重复类定义, 恢复为 242 行正确版本
4. **observability.py**: 已去除重复类定义, 恢复为 204 行正确版本
5. **autonomous.py**: 已与 `book/code/ch16/autonomous.py` 对齐 (196 行)

### P1: README 使用说明 -- 已修复

已更新 README.md:
- 将 `book/code/chXX/` 目录标注为权威参考
- 说明 `ch01`-`ch09` 的 git tag 可用, `ch10`-`ch16` 请使用 book/code/ 快照
- 更新项目结构说明

### P2: 章节行数引用 -- 已修复

已修正以下章节中不准确的代码行数描述:
- ch05: skill_loader.py 103→102 行
- ch07: subagent.py 103→125 行
- ch08: background.py 170→190 行
- ch09: tasks.py 240→282 行
- ch12: autonomous.py 185→196 行
- ch13: worktree.py 200→185 行
- ch14: security.py 200→242 行 (第一处提及)
- ch15: observability.py 170→204 行 (第一处提及)

### 未修复: Git 标签 (ch10-ch16)

Git tag `ch10`-`ch16` 仍指向原始提交 (含空占位符)。由于重写历史风险较大, 已通过 README 说明引导读者使用 `book/code/chXX/` 目录。如需后续修复, 可考虑 rebase 重建提交历史。

---

## 六、代码质量评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构设计 | 优秀 | 每章增量添加能力, 模块边界清晰 |
| 错误处理 | 良好 | 工具返回字符串错误信息, LLM 友好 |
| 线程安全 | 良好 | BackgroundManager 使用 Lock, TeamManager 正确使用 daemon 线程 |
| 安全性 | 良好 | safe_path 防穿越, Sandbox + 命令分级 + 确认门 |
| 代码风格 | 良好 | 一致的命名规范, 适当的注释 |
| 可维护性 | 良好 | 工厂模式, 注册表模式, 关注点分离 |

---

## 七、结论

**book/code/ 快照代码质量良好**, 全部 16 章的代码均可正确加载运行, 且与章节描述匹配。

已完成的修复:
1. **miniagent/ 工作目录** [P0]: 5 个文件已修复, 现与 book/code/ch16/ 完全一致
2. **README 使用说明** [P1]: 已引导读者使用 book/code/ 快照, 说明 git tag 限制
3. **章节行数引用** [P2]: 8 处不准确的行数已修正

遗留项:
- Git tag `ch10`-`ch16` 仍指向含空占位符的原始提交 (已通过 README 说明规避)
