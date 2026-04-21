# 参考文献

## 官方文档

- Anthropic. "Skill Authoring Best Practices." Claude Platform Documentation. https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Anthropic. "Equipping Agents for the Real World with Agent Skills." Anthropic Engineering Blog. https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

## 社区资源

- the911fund. "skill-of-skills: The curated directory for AI coding skills." GitHub. https://github.com/the911fund/skill-of-skills
- Travis VN. "awesome-claude-skills: A curated list of awesome Claude Skills." GitHub. https://github.com/travisvn/awesome-claude-skills
- sanshao85. "Claude Skills 开发完全指南." GitHub. https://github.com/sanshao85/claude-skills-guide
- obra. "superpowers: 20+ Skills for Claude Code." GitHub.

## Skill 案例引用

- Karpathy, Andrej. Claude Code Skills 集合. GitHub.
- Trail of Bits. "Security Skills: CodeQL and Semgrep integration for AI agents." GitHub.
- lovstudio. "lovstudio/skills: 33 个分类管理的商业级 Skill 生态." GitHub. https://github.com/lovstudio/skills
  - 第 11 章案例 4-6 的核心来源：any2deck（强制交互模式）、skill-optimizer（自动化质量管线）、any2pdf（踩坑记录模式）
  - 第 12 章生态架构分析：独立仓库 + 中央索引、扩展 Frontmatter、付费/免费混合分发
- lovstudio. "any2deck: 将任何内容转换为演示幻灯片." GitHub. https://github.com/lovstudio/skills/tree/main/any2deck
  - 第 11 章引用：AskUserQuestion 强制交互、进度 Checklist、16 种风格系统
- lovstudio. "skill-optimizer: 自动审计和优化 SKILL.md 质量." GitHub. https://github.com/lovstudio/skills/tree/main/skill-optimizer
  - 第 11 章引用：Lint→Fix→Bump→Changelog 自动化管线
- lovstudio. "any2pdf: Markdown 到 PDF 转换器." GitHub. https://github.com/lovstudio/skills/tree/main/any2pdf
  - 第 11 章引用："Hard-Won Lessons" 踩坑记录设计模式
- lovstudio. "skill-creator: Skill 创建元技能." GitHub. https://github.com/lovstudio/skills/tree/main/skill-creator
  - 第 12 章引用：仓库级 skill-creator 与本书轻量版的对比分析

## 书籍

- Gawande, Atul. *The Checklist Manifesto: How to Get Things Right.* Metropolitan Books, 2009.
  - 第 9 章引用：清单在复杂系统中的价值

- 斋藤康毅. *深度学习入门：自制框架 (Deep Learning from Scratch 3).* 人民邮电出版社, 2021.
  - 本书方法论灵感来源之一：渐进式从零构建的教学法

- Manning, Christopher D., Prabhakar Raghavan, and Hinrich Schütze. *Introduction to Information Retrieval.* Cambridge University Press, 2008.
  - 第 2 章引用：精确率 vs 召回率的权衡适用于 description 设计

## 规范与标准

- Conventional Commits. "A specification for adding human and machine readable meaning to commit messages." https://www.conventionalcommits.org/
  - 第 3 章 `commit-message` Skill 采用的提交信息规范

- Keep a Changelog. "Don't let your friends dump git logs into changelogs." https://keepachangelog.com/
  - 第 12 章 `changelog-writer` 示例采用的格式

- OpenAPI Specification. "The OpenAPI Specification (OAS) defines a standard interface description for HTTP APIs." https://spec.openapis.org/oas/latest.html
  - 第 4 章 `api-doc-writer` Skill 的输出格式参考

## 学术研究

- Li, Junhao, et al. "Agent Skill: A Comprehensive Survey on Skill Acquisition for AI Agents." arXiv:2602.12430, 2025.
  - 第 1 章和第 12 章引用：Skill 获取方法论全景图

- Wang, Yi, et al. "EvoSkill: Evolving Agent Skills from Failure Trajectories." arXiv:2603.02766, 2025.
  - 第 12 章引用：失败驱动的 Skill 自动发现

- Xu, Yiwei, et al. "EvoSkills: Co-Evolving Skill Generators and Verifiers." arXiv:2604.01687, 2025.
  - 第 9 章和第 12 章引用：Generator-Verifier 隔离，性能 32%→75%

- Chen, Zifan, et al. "SkillForge: Enterprise-Grade Skill Generation." arXiv:2604.08618, 2025.
  - 第 10 章和第 12 章引用：四维诊断框架、知识饱和曲线

## Skill 生态仓库

- Vercel Labs. "agent-skills: Official Vercel Agent Skills Collection." GitHub. https://github.com/vercel-labs/agent-skills
  - 第 7 章引用：脚本优先原则、上下文效率最佳实践

- Orchestra Research. "AI-research-SKILLs: 95 Skills for AI Research." GitHub. https://github.com/Orchestra-Research/AI-research-SKILLs
  - 第 12 章引用：双循环研究架构、22 个领域分类

- numman-ali. "openskills: Universal Skills Loader." GitHub. https://github.com/numman-ali/openskills
  - 第 12 章引用：跨平台 Skill 兼容性

- heilcheng. "awesome-agent-skills: Cross-Platform Agent Skill Index." GitHub. https://github.com/heilcheng/awesome-agent-skills
  - 第 12 章引用：2026 生态趋势

- Agent Skills Specification. "agentskills.io." https://agentskills.io/specification
  - 第 12 章引用：跨平台标准化

## 测试与评估

- Promptfoo. "LLM 评估和测试框架." https://promptfoo.dev/
  - 第 10 章引用：断言分类体系、加权断言、skill-used 断言

## 文章与博客

- Hightower, Richard. "Claude Code: How to Build, Evaluate, and Tune AI Agent Skills." Medium, 2025.
- Pessan, Julio. "SkillsMP: This 96,751+ Claude Code Skills Directory." Medium, 2025.
- "Claude Skills and Subagents: Escaping the Prompt Engineering Hamster Wheel." Towards Data Science, 2025.

## 设计原则

- Pike, Rob. "Notes on Programming in C." 1989.
  - Unix 管道哲学："一个程序只做一件事，做好它"——Multi-Pass 设计的灵感

- Command Line Interface Guidelines. https://clig.dev/
  - 第 5 章命令设计的参考资源
