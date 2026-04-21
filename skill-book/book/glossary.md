# 术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| **Skill** | Skill | 一个结构化的指令文件（SKILL.md），告诉 Agent "当你需要做某件事时，按照这些步骤来"。由 YAML Frontmatter 和 Markdown 正文组成。 |
| **SKILL.md** | SKILL.md | Skill 的核心文件。包含 YAML Frontmatter（元数据）和 Markdown Body（指令正文）。 |
| **YAML Frontmatter** | YAML Frontmatter | SKILL.md 开头两行 `---` 之间的元数据块，包含 `name` 和 `description` 字段。 |
| **description** | description | YAML Frontmatter 中的描述字段。Agent 在 Layer 1 唯一能看到的信息，决定了 Skill 的加载时机。 |
| **两层注入** | Two-layer Injection | Skill 系统的核心架构。Layer 1 在上下文中常驻轻量摘要（~100 tokens/skill），Layer 2 按需加载完整内容。 |
| **Layer 1** | Layer 1 | Skill 的第一层——name + description 的轻量摘要，始终在 Agent 上下文中。 |
| **Layer 2** | Layer 2 | Skill 的第二层——SKILL.md 的完整正文，Agent 决定加载时才读入。 |
| **Layer 3** | Layer 3 | Skill 的第三层——scripts/、reference/、templates/ 中的辅助文件，执行过程中按需读取。 |
| **Multi-Pass** | Multi-Pass | 多步工作流设计模式。把复杂任务拆成多个阶段（Pass），每个 Pass 只做一件事，通过交接文件传递信息。 |
| **交接文件** | Artifact | Multi-Pass 中 Pass 之间传递信息的中间文件。确保信息不依赖 Agent 记忆。 |
| **暂停点** | Checkpoint | Multi-Pass 中设置的用户确认点。在关键 Pass 后暂停，等待用户确认方向后再继续。 |
| **命令表** | Command Table | SKILL.md 中的 Markdown 表格，声明 Skill 支持的多个子命令及其用途。 |
| **命令路由** | Command Routing | Agent 根据用户请求匹配命令表中的子命令，执行对应的指令逻辑。 |
| **示例锚定** | Example Anchoring | 通过具体的输入/输出对来固定 Agent 行为的技巧。包括输入/输出示例、输出模板、反例三种方式。 |
| **输出模板** | Output Template | 固定格式的输出框架，变量部分用占位符标记。Agent 按模板生成输出。 |
| **反例** | Counter-example | 展示错误输出并解释为什么错的锚定方式。Agent 会避免生成类似反例的输出。 |
| **三层架构** | Three-layer Architecture | 将 Skill 内容分散到 SKILL.md（核心指令）+ scripts/（确定性脚本）+ reference/（参考文档）的设计模式。 |
| **工具编排** | Tool Orchestration | 在 Skill 中明确声明每个步骤使用什么工具、按什么顺序、在什么条件下执行。 |
| **Quality Checklist** | Quality Checklist | 内置在 Skill 中的可验证检查项列表，Agent 在输出前逐项自检。 |
| **元技能** | Meta-Skill | 创建其他 Skill 的 Skill。把 Skill 创作方法论编码为可执行的指令。 |
| **触发准确性** | Trigger Accuracy | Skill 质量维度之一：该加载时加载，不该时不加载的能力。 |
| **执行一致性** | Execution Consistency | Skill 质量维度之一：同样输入下输出质量的稳定程度。 |
| **Token 效率** | Token Efficiency | Skill 质量维度之一：用最少的 tokens 达到预期效果的能力。 |
| **脆弱度** | Fragility | 任务对输出精确性的要求程度。高脆弱度任务（如配置生成）需要低自由度的精确指令。 |
| **渐进式加载** | Progressive Disclosure | 根据需要逐步加载更多信息的设计原则。Skill 系统的三层架构就是渐进式加载的实践。 |
| **Agent** | Agent | 能理解自然语言、自主调用工具、执行多步任务的 AI 系统。Skill 是 Agent 的知识扩展机制。 |
| **Harness** | Harness | Agent 除 LLM 模型之外的所有组件——工具、上下文管理、知识加载等。Skill 是 Harness 的关键组件。 |
| **System Prompt** | System Prompt | Agent 启动时加载的全局指令。Skill 的 Layer 1 摘要会追加到 System Prompt 末尾。 |
| **上下文窗口** | Context Window | LLM 能处理的最大 token 数。Skill 设计需要考虑上下文预算。 |
| **Conventional Commits** | Conventional Commits | Git 提交信息的格式规范：`type(scope): description`。本书 `commit-message` Skill 采用的格式。 |
| **SOP** | Standard Operating Procedure | 标准操作流程。Skill 本质上就是给 Agent 的 SOP。 |
| **扩展 Frontmatter** | Extended Frontmatter | 在标准 name + description 之外添加 category、tagline、version、tags、compatibility 等字段的 YAML Frontmatter。用于支撑 Skill 生态的分类、搜索和版本管理。 |
| **强制交互** | Mandatory AskUserQuestion | 一种设计模式：在 Skill 执行任何操作之前，强制使用 AskUserQuestion 工具确认用户意图。适用于选项空间大的 Skill。 |
| **踩坑记录** | Hard-Won Lessons | 一种 Skill 设计模式：在 SKILL.md 中记录实际使用中遇到的陷阱和解决方案。填补 LLM 训练数据中缺失的特定领域调试经验。 |
| **进度 Checklist** | Progress Checklist | 与 Quality Checklist 不同，用于追踪 Skill 执行进度而非输出质量。让用户实时看到 Agent 完成了哪些步骤。 |
| **Skill 生态** | Skill Ecosystem | 多个 Skill 通过统一的索引、分类、版本管理组织成的系统。如 lovstudio 的 33-Skill 生态。 |
| **Pre-fill from Context** | Pre-fill from Context | 一种设计模式：Agent 先从已有上下文（用户记忆、已读文件等）预填信息，再让用户确认和补充，减少交互轮次。 |
| **欠触发** | Under-triggering | 模型倾向于不加载 Skill 的现象。Agent 把 Skill 视为"额外工作"，优先用内置知识。解决方案是让 description 稍微"pushy"。 |
| **Pushy Description** | Pushy Description | 一种 description 写作策略：明确列出触发场景，甚至写"even if they don't explicitly ask"，对抗模型的欠触发倾向。 |
| **自由度匹配** | Freedom Calibration | 根据任务类型选择指令精确度的方法论。窄桥型任务（配置生成）需要低自由度指令；开阔地型任务（创意写作）需要高自由度指令。 |
| **窄桥型任务** | Narrow-Bridge Task | 只有一条正确路径的任务（如配置文件生成、格式转换）。需要精确指令和模板锚定，自由度应降到最低。 |
| **开阔地型任务** | Open-Field Task | 有多条合理路径的任务（如创意写作、架构设计）。应给出方向和约束，但保留 Agent 的决策空间。 |
| **Guardrails** | Guardrails | Skill 中的防护栏设计：告诉 Agent 不该做什么，包括 Anti-Patterns 清单、安全模型、权限边界。防御性设计的核心组件。 |
| **Generator-Verifier 隔离** | Generator-Verifier Isolation | 将生成输出和验证输出分离给不同 Agent 的架构模式。EvoSkills 发现隔离后性能从 32% 跳到 75%。打破确认偏误的关键技术。 |
| **断言分类体系** | Assertion Taxonomy | Promptfoo 的三层测试断言框架：确定性断言（contains, is-json）、轨迹断言（tool-used, tool-sequence）、模型辅助断言（llm-rubric, factuality）。 |
| **Description 优化循环** | Description Optimization Loop | 系统化优化 description 的方法：生成 20 个评估查询 → 60/40 训练/测试分割 → 每查询 3 次运行 → 最多 5 轮迭代 → 按测试集分数选最佳。 |
| **四维诊断** | Four-Dimensional Diagnosis | SkillForge 的 Skill 问题诊断框架，从知识、工具使用、澄清策略、语气风格四个维度并行分析 Skill 缺陷。 |
| **知识饱和曲线** | Knowledge Saturation Curve | 迭代优化的收益递减规律：知识修复 2-3 轮后收益递减，工具和风格修复则持续改进。连续两轮测试集改进 <2% 时应停止迭代。 |
| **脚本优先** | Scripts-First | Vercel 生态的设计哲学：将确定性操作封装为脚本放入 scripts/ 目录。脚本执行不消耗上下文（只有 stdout 进入对话），大幅节省 token。 |
| **Worker/Judge** | Worker/Judge | 循环反馈工作流模式：Worker Agent 执行任务，Judge Agent 评判结果，不合格则循环重试。来自 checkmate 的安全分离架构。 |
| **量化决策矩阵** | Quantified Decision Matrix | 一种工作流模式：为每个选项在多个维度上打分（0-10），乘以权重汇总，选择总分最高的选项。消除主观决策偏差。 |
| **诊断-修复-验证** | Diagnose-Fix-Verify | 一种工作流模式：先诊断问题根因，修复后验证结果，统一模式跨多种场景复用。emergency-rescue 用此模式覆盖 20+ 场景。 |
