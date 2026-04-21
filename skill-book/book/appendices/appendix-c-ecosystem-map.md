# 附录 C：全球 Skill 生态资源地图

> 截至 2026 年 4 月，Skill 已成为跨平台 Agent 知识扩展的事实标准。本附录汇总主要资源，帮助读者快速找到所需的 Skill、平台和社区。

---

## C.1 主要 Skill 集合仓库

| 仓库 | Stars | 定位 | 技能数量 |
|------|-------|------|---------|
| **vercel-labs/agent-skills** | 25K+ | Vercel 官方 Skills，聚焦部署与前端 | 20+ |
| **numman-ali/openskills** | 9K+ | 通用 Skills 加载器，兼容所有 Agent | 框架层 |
| **Orchestra-Research/AI-research-SKILLs** | 7K+ | AI 研究领域专业 Skills | 95 |
| **VoltAgent/awesome-openclaw-skills** | 5K+ | OpenClaw 社区精选索引 | 5,400+ |
| **heilcheng/awesome-agent-skills** | 4K+ | 跨平台 Agent Skill 索引 | 200+ |
| **xstongxue/best-skills** | 1K+ | 中文精选高质量 Skills 合集 | 12 |
| **the911fund/skill-of-skills** | — | Skill 目录聚合 | 686+ |
| **travisvn/awesome-claude-skills** | — | Claude Skills 精选列表 | — |

---

## C.2 官方平台 Skill 集合

### Anthropic 官方 (16 个)

Skills 标准的"黄金模板"，代表最佳实践参考。

| Skill | 功能 |
|-------|------|
| `pdf` / `docx` / `xlsx` / `pptx` | 办公文档全功能处理 |
| `skill-creator` | 创建新 Skills 的元技能（本书第 12 章核心参考） |
| `frontend-design` | 前端设计与 UI/UX 开发 |
| `mcp-builder` | 创建 MCP 服务器以集成外部 API |
| `webapp-testing` | 使用 Playwright 测试本地 Web 应用 |
| `canvas-design` / `algorithmic-art` | 视觉艺术与生成艺术 |
| `doc-coauthoring` / `internal-comms` | 协作写作与内部沟通 |

### OpenAI Codex 官方 (18 个)

| Skill | 功能 |
|-------|------|
| `cloudflare-deploy` / `netlify-deploy` | 云平台自动化部署 |
| `figma` / `figma-implement-design` | 设计稿到生产代码 |
| `playwright` | 真实浏览器自动化 |
| `sora` / `imagegen` / `speech` | 多模态内容生成 |
| `gh-fix-ci` / `gh-address-comments` | GitHub 工作流自动化 |
| `jupyter-notebook` | 可复现 Notebook 创建 |

### Google Gemini 官方 (4 个)

| Skill | 功能 |
|-------|------|
| `gemini-api-dev` | Gemini API 应用开发 |
| `vertex-ai-api-dev` | Vertex AI 上的 Gemini 应用 |
| `gemini-live-api-dev` | 实时双向流式应用 |
| `gemini-interactions-api` | 多模态交互 API |

### HuggingFace 官方 (4 个)

| Skill | 功能 |
|-------|------|
| `hf-cli` | HuggingFace CLI 操作 |
| `hugging-face-datasets` | 数据集创建与 SQL 查询 |
| `hugging-face-model-trainer` | TRL 模型训练 (SFT/DPO/GRPO) |
| `transformers.js` | 浏览器端 ML 推理 |

---

## C.3 兼容平台矩阵 (2026)

SKILL.md 格式已被以下 9 个主要平台采纳：

| 平台 | 厂商 | 发现机制 |
|------|------|---------|
| Claude Code | Anthropic | `<available_skills>` XML |
| Claude.ai | Anthropic | 项目级 Skills |
| Codex | OpenAI | `AGENTS.md` + Skills 目录 |
| GitHub Copilot | GitHub/Microsoft | `.github/skills/` |
| VS Code Copilot | Microsoft | 工作区 Skills |
| Antigravity | Google | 兼容 SKILL.md |
| Gemini CLI | Google | 兼容 SKILL.md |
| Kiro | AWS | 兼容 SKILL.md |
| Junie | JetBrains | 兼容 SKILL.md |

**跨平台兼容要点**：一个写得好的 SKILL.md 可以不经修改在多个平台上运行。关键是避免依赖平台特有的工具名称（如用通用描述替代 `mcp__xxx` 前缀）。

---

## C.4 重点仓库速览

### Vercel Agent Skills (25K Stars)

- **核心贡献**：脚本优先原则（Scripts-First）、上下文效率最佳实践
- **设计规范**：SKILL.md < 500 行、脚本用 `set -e` + stderr 状态 + stdout JSON
- **本书引用**：第 7 章 §7.3 脚本优先原则

### Orchestra Research (7K Stars)

- **核心贡献**：双循环研究架构（Bootstrap → Inner Loop → Outer Loop → Finalize）
- **规模**：95 个 SKILL.md 覆盖 22 个 AI 研究领域
- **设计哲学**："Quality over Quantity"、完全自主运行、状态持久化
- **本书引用**：第 12 章 §12.8 全球生态

### OpenSkills (9K Stars)

- **核心贡献**：通用 Skills 加载器，不绑定特定 Agent 平台
- **创新**：统一的 Skill 发现与加载协议
- **本书引用**：第 12 章 §12.8 跨平台标准

### OpenClaw 社区 (5K+ Skills)

- **核心贡献**：TOP 30 精选 Skills、最佳实践文档
- **本书引用**：第 3-4、7、9、11 章大量案例

---

## C.5 Skill 发现工具与平台

| 工具/平台 | 用途 |
|-----------|------|
| `npx skills` (Vercel) | CLI 搜索和安装 Skills |
| agentskills.io | Skills 格式规范与社区索引 |
| OpenClaw 市场 | 社区 Skill 浏览与安装 |
| skill-of-skills | Skill 聚合目录 |
| awesome-agent-skills | 跨平台精选索引 |

---

## C.6 学术与前沿研究

| 论文/项目 | 关键贡献 | 本书章节 |
|-----------|---------|---------|
| EvoSkill (arxiv.org/abs/2603.02766) | 从 Agent 失败中自动发现 Skill | Ch12 §12.7 |
| EvoSkills (arxiv.org/html/2604.01687v1) | Generator-Verifier 共进化 | Ch9 §9.7, Ch12 §12.7 |
| SkillForge (arxiv.org/html/2604.08618v1) | 四维诊断 + 企业数据驱动 | Ch10 §10.5, Ch12 §12.7 |
| Agent Skills 综述 (arxiv.org/abs/2602.12430) | Skill 获取方法论全景 | Ch1 §1.1, Ch12 §12.7 |
| Promptfoo | 断言体系 + 评估框架 | Ch10 §10.2 |

---

## C.7 本书案例来源索引

快速查找本书中引用的所有外部 Skill 案例：

| Skill 名称 | 来源 | 本书章节 |
|------------|------|---------|
| `deslop` | OpenClaw/brennerspear | Ch11 §11.8 |
| `emergency-rescue` | OpenClaw/gitgoodordietrying | Ch4 §4.5, Ch11 §11.8 |
| `checkmate` | OpenClaw/insipidpoint | Ch4 §4.6, Ch11 §11.8 |
| `anti-pattern-czar` | OpenClaw/glucksberg | Ch4 §4.7 |
| `adaptive-reasoning` | OpenClaw/enzoricciulli | Ch4 §4.8 |
| `conventional-commits` | OpenClaw/bastos | Ch3 |
| `agent-self-reflection` | OpenClaw/brennerspear | Ch9 §9.6 |
| `client-flow` | OpenClaw/ariktulcha | Ch4 §4.5 |
| skill-creator (Anthropic) | Anthropic 官方 | Ch12 §12.6 |
| Trail of Bits Security | Trail of Bits | Ch11 (planned) |
| obra/superpowers | obra | Ch11 (planned) |
| lovstudio/skills | lovstudio | Ch11 §11.4-11.6 |
