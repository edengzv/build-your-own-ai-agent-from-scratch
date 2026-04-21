# 全球 Agent Skills 生态全景调研 (补充篇)

> 在 OpenClaw Skills 调研基础上，进一步覆盖全球主要 Skills 生态
> 调研时间：2026-04-19

---

## 一、全球 Skills 生态版图

### 1.1 主要 Skills 集合仓库一览

| 仓库 | Stars | 定位 | 技能数量 |
|------|-------|------|---------|
| **vercel-labs/agent-skills** | 25,342 | Vercel 官方 Skills 集合，聚焦部署与前端 | 20+ |
| **vercel-labs/skills** | 14,587 | 开放 Skills 生态 CLI 工具 (`npx skills`) | 工具层 |
| **numman-ali/openskills** | 9,830 | 通用 Skills 加载器，兼容所有 Agent | 框架层 |
| **Orchestra-Research/AI-research-SKILLs** | 7,071 | AI 研究领域专业 Skills，95 个 SKILL.md | 95 |
| **VoltAgent/awesome-openclaw-skills** | ~5,000 | OpenClaw 社区精选索引，30 个分类 | 5,400+ |
| **heilcheng/awesome-agent-skills** | 4,109 | 跨平台 Agent Skill 索引，含官方+社区 | 200+ |
| **xstongxue/best-skills** | 1,042 | 中文通用高质量 Skills 合集 | 12 |
| **jdrhyne/agent-skills** | 227 | 多平台 Agent Skills 与 Prompts 集合 | 50+ |

### 1.2 官方平台 Skills（一手来源）

#### Anthropic 官方 Skills (16个)
由 Anthropic 官方维护，代表 Skills 标准的"黄金模板"：

| Skill | 功能 |
|-------|------|
| `pdf` | PDF 全功能处理：提取文本、创建、合并、表单 |
| `docx` | Word 文档的创建、编辑、分析 |
| `xlsx` | Excel 电子表格处理与分析 |
| `pptx` | PowerPoint 演示文稿处理 |
| `doc-coauthoring` | 协作文档编辑与共同创作 |
| `frontend-design` | 前端设计与 UI/UX 开发 |
| `web-artifacts-builder` | 用 React + Tailwind 构建复杂 HTML artifacts |
| `canvas-design` | PNG/PDF 格式的视觉艺术设计 |
| `algorithmic-art` | 用 p5.js 创建生成艺术 |
| `mcp-builder` | 创建 MCP 服务器以集成外部 API |
| `webapp-testing` | 使用 Playwright 测试本地 Web 应用 |
| `skill-creator` | 创建新 Skills 的指南 |
| `theme-factory` | 专业主题样式生成 |
| `slack-gif-creator` | 为 Slack 优化的 GIF 动画创建 |
| `brand-guidelines` | Anthropic 品牌色彩与排版应用 |
| `internal-comms` | 状态报告、新闻稿、FAQ 撰写 |

#### OpenAI Codex 官方 Skills (18个)

| Skill | 功能 |
|-------|------|
| `cloudflare-deploy` | Cloudflare Workers/Pages 部署 |
| `develop-web-game` | 使用 Playwright 迭代构建 Web 游戏 |
| `doc` | .docx 文档读写与格式化 |
| `gh-address-comments` | 处理 GitHub PR 审查评论 |
| `gh-fix-ci` | 修复失败的 GitHub Actions CI |
| `imagegen` | OpenAI Image API 图像生成 |
| `jupyter-notebook` | 创建可复现的 Jupyter Notebook |
| `linear` | Linear 项目管理与工作流 |
| `netlify-deploy` | Netlify 自动化部署 |
| `notion-knowledge-capture` | 会话内容转 Notion Wiki |
| `pdf` | PDF 读写与审查 |
| `playwright` | 真实浏览器自动化交互 |
| `sora` | Sora API 视频生成 |
| `speech` | OpenAI TTS 语音合成 |
| `spreadsheet` | 电子表格操作与可视化 |
| `figma` | Figma MCP 设计上下文获取 |
| `figma-implement-design` | Figma 设计稿转生产代码 |
| `frontend-skill` | 创建视觉强的落地页与 Web 应用 |

#### Google Gemini 官方 Skills (4个)

| Skill | 功能 |
|-------|------|
| `gemini-api-dev` | Gemini API 应用开发最佳实践 |
| `vertex-ai-api-dev` | Vertex AI 上的 Gemini 应用开发 |
| `gemini-live-api-dev` | 实时双向流式应用构建 |
| `gemini-interactions-api` | 文本/聊天/流式/图像生成交互 |

#### HuggingFace 官方 Skills (4个)

| Skill | 功能 |
|-------|------|
| `hf-cli` | HuggingFace CLI 工具操作 |
| `hugging-face-datasets` | 数据集创建与 SQL 查询 |
| `hugging-face-model-trainer` | TRL 模型训练：SFT/DPO/GRPO |
| `transformers.js` | 浏览器端 ML 模型运行 |

### 1.3 兼容平台矩阵 (2026)

Skills 已成为跨平台标准，兼容以下 9 个主要 Agent 平台：

| 平台 | 厂商 |
|------|------|
| Claude Code | Anthropic |
| Claude.ai | Anthropic |
| Codex | OpenAI |
| GitHub Copilot | GitHub/Microsoft |
| VS Code Copilot | Microsoft |
| Antigravity | Google |
| Gemini CLI | Google |
| Kiro | AWS |
| Junie | JetBrains |

---

## 二、重点仓库深度分析

### 2.1 Orchestra Research — AI 研究 Skills (7,071 Stars)

**定位**: AI 研究领域的专业 Skills 库，95 个 SKILL.md 覆盖 AI 研究全生命周期。

**核心架构创新 — 双循环研究引擎 (Two-Loop Architecture)**:

```
BOOTSTRAP（一次性，轻量级）
  界定问题 → 文献搜索 → 形成初始假设

INNER LOOP（快速、自主、循环）
  选择假设 → 实验 → 测量 → 记录 → 学习 → 下一个
  目标：运行有约束的实验，产出可测量结果

OUTER LOOP（周期性、反思性）
  审查结果 → 发现模式 → 更新发现 → 新假设 → 决定方向
  目标：综合理解，发现故事 — 新颖性由此产生

FINALIZE（结题时）
  通过 ml-paper-writing 写论文 → 最终演示 → 归档
```

**22 个领域分类**:

| 编号 | 领域 | 包含 Skills |
|------|------|------------|
| 00 | Autoresearch（研究编排） | 核心编排 Skill，管理全流程 |
| 01 | Model Architecture | LitGPT, Mamba, NanoGPT, RWKV, TorchTitan |
| 02 | Tokenization | HuggingFace Tokenizers, SentencePiece |
| 03 | Fine-Tuning | Axolotl, LLaMA-Factory, PEFT, Unsloth |
| 04 | Mechanistic Interpretability | NNsight, Pyvene, SAELens, TransformerLens |
| 05 | Data Processing | Ray Data, NeMo Curator |
| 06 | Post-Training | TRL, GRPO, OpenRLHF, verl, SimPO 等8个 |
| 07 | Safety & Alignment | Constitutional AI, LlamaGuard, NeMo Guardrails |
| 08 | Distributed Training | Megatron-Core, DeepSpeed, FSDP |
| 09 | Infrastructure | Modal, SkyPilot, Lambda Labs |
| 10 | Optimization | Flash Attention, GGUF 量化 |
| 11 | Evaluation | 通用/代码评估基准 |
| 12 | Inference & Serving | vLLM, TensorRT-LLM, SGLang |
| 13 | MLOps | 实验追踪、模型注册 |
| 14 | Agents | LangChain, LlamaIndex, CrewAI |
| 15 | RAG | Chroma, Qdrant 等向量数据库 |
| 16 | Prompt Engineering | 声明式编程、约束生成 |
| 17 | Observability | AI 应用追踪与评估 |
| 18 | Multimodal | 视觉、音频、图像生成 |
| 19 | Emerging Techniques | MoE、蒸馏、模型合并 |
| 20 | ML Paper Writing | LaTeX 模板、引用验证 |
| 21 | Research Ideation | 头脑风暴、创意思维框架 |

**设计哲学关键词**: "Quality over Quantity"、"深度优于广度"、每个模块包含生产级代码、故障排查步骤、官方文档链接。

**Autoresearch Skill 的精髓设计**:
- **完全自主运行**: "Do not ask the user for permission — use your best judgment and keep moving"
- **状态持久化**: `research-state.yaml` 作为中央状态追踪
- **工作区规范**: 预定义 8 个目录（literature/, src/, data/, experiments/, paper/ 等）
- **意图解析表**: 根据用户状态（模糊想法/清晰问题/已有计划/恢复中断）决定行动
- **代码复用原则**: "When you write useful code, move it to src/ so it can be reused across experiments"

### 2.2 Vercel Agent Skills — 部署生态 (25,342 Stars)

**定位**: Vercel 官方 Skills 集合，聚焦 Web 开发与部署工作流。

**SKILL.md 编写标准（来自 CLAUDE.md）**:

```markdown
## 关键规范

1. 目录结构:
   skills/{skill-name}/           # kebab-case
     SKILL.md                     # 必须
     scripts/{script-name}.sh     # 必须：可执行脚本
   {skill-name}.zip               # 必须：打包分发

2. 脚本规范:
   - 使用 #!/bin/bash shebang
   - 使用 set -e 快速失败
   - 状态消息写到 stderr: echo "Message" >&2
   - 机器可读输出(JSON) 写到 stdout
   - 包含临时文件的 cleanup trap

3. 上下文效率最佳实践:
   - SKILL.md < 500 行
   - 写精确的 description
   - 使用渐进式披露
   - 优先用脚本而非内联代码
   - 文件引用只有一层深度
```

**新增洞察 — "脚本优先"原则**:
> "Prefer scripts over inline code — script execution doesn't consume context (only output does)"

这是 Vercel 生态独特的设计哲学：将确定性操作封装为 Bash 脚本放入 `scripts/` 目录，Agent 执行脚本而非在上下文中生成代码，大幅节省 token 消耗。

### 2.3 OpenSkills — 通用 Skills 加载器 (9,830 Stars)

**定位**: 将 Anthropic 的 Skills 系统带到每一个 AI 编码 Agent。

**核心价值**: "One CLI. Every agent. Same format as Claude Code."

**工作原理**:
1. 将 Skills 安装到 `.claude/skills/` 目录
2. 在 `AGENTS.md` 中生成 `<available_skills>` XML 块
3. 任何能读取 `AGENTS.md` 的 Agent 都能使用 Skills
4. Agent 通过 `npx openskills read <skill-name>` 加载技能

**兼容性设计（Claude Code vs OpenSkills）**:

| 方面 | Claude Code | OpenSkills |
|------|-------------|------------|
| 提示格式 | `<available_skills>` XML | 完全相同 |
| 存储位置 | `.claude/skills/` | `.claude/skills/`（默认） |
| 调用方式 | `Skill("name")` 工具 | `npx openskills read <name>` |
| 技能市场 | Anthropic marketplace | GitHub 仓库 |
| 渐进式披露 | 支持 | 支持 |

**通用模式安装**:
```bash
npx openskills install anthropics/skills --universal
# 安装到 .agent/skills/ 避免与 Claude 插件市场冲突
```

**优先级顺序**:
1. `./.agent/skills/`
2. `~/.agent/skills/`
3. `./.claude/skills/`
4. `~/.claude/skills/`

### 2.4 xstongxue/best-skills — 中文高质量合集 (1,042 Stars)

**定位**: 面向中文用户的通用高质量 Skills 合集，12 个精选 Skill。

**分类**:

| 类别 | Skills |
|------|--------|
| 学术论文写作 | paper-write, codegen-doc, pptgen-drawio, drawio-diagram, codegen-diagram |
| 软件开发生命周期 | dev-workflow（5阶段流程）, code-review-skill |
| 内容创作 | wechat-article-writer, md-report-summary |
| 工具转换 | skill-create, skill-prompt-convert, excalidraw-diagram |

**设计亮点**:
- `dev-workflow` 覆盖完整软件开发5阶段：需求分析→方案设计→实现→代码审查→调试
- `skill-prompt-convert` 独特功能：将 Skill 文件转换为手动聊天提示词
- `wechat-article-writer` 支持 9 种文风（技术教程、观点分析等）
- 每个 Skill 都有预览图，直观展示效果

### 2.5 heilcheng/awesome-agent-skills — 跨平台索引 (4,109 Stars)

**定位**: 社区维护的 Agent Skill 总目录，强调"真实团队使用"的质量标准。

**独特贡献 — 2026 趋势洞察**:

1. **自主执行 (Autonomous Execution)**: Agent 从"提示-响应"模型进化为分解目标、权衡取舍、独立执行多步骤计划
2. **多 Agent 编排 (Multi-Agent Orchestration)**: 由专业 Agent 团队（文档、测试、编码）协作，Manager Agent 综合交付物并解决冲突
3. **Agentic IDE**: Cursor、Windsurf、Claude Code 进化为"全Agent IDE"，Agent 原生执行终端命令、监控遥测、管理文件
4. **领域专用 Skills 规模化**: 组织从通用提示转向高度专业化的 Skills，减少幻觉，提高生产部署可靠性

**质量标准 — 区别于批量生成的仓库**:
> "Unlike bulk-generated skill repositories, this collection focuses on real-world Agent Skills created and used by actual engineering teams."

**技能发现工具推荐**:
- **SkillsMP Marketplace** (skillsmp.com): 自动索引 GitHub 上所有 Skill 项目
- **skills.sh** (Vercel): 排行榜，查看最流行的 Skills
- **npx skills CLI** (vercel-labs/skills): 命令行技能管理

---

## 三、新发现的设计模式与最佳实践

### 3.1 脚本优先原则 (Scripts-First)
**来源**: Vercel Agent Skills

> "Prefer scripts over inline code — script execution doesn't consume context (only output does)"

将确定性操作封装为 Bash/Python 脚本，Agent 仅执行脚本并读取输出，而非在上下文中生成代码。

**脚本编写规范**:
```bash
#!/bin/bash
set -e                        # 快速失败
echo "Status message" >&2     # 状态消息 → stderr
echo '{"result": "data"}'     # 机器可读输出 → stdout (JSON)
trap 'rm -f "$tmpfile"' EXIT  # 清理临时文件
```

**效果**: 大幅降低 token 消耗，因为脚本代码不占用上下文窗口。

### 3.2 双循环架构 (Two-Loop Architecture)
**来源**: Orchestra Research Autoresearch

适用于需要长期运行的复杂任务（如研究项目、大型重构）：

```
内循环 (Inner Loop) — 快速、聚焦
  ↓ 选择假设 → 实验 → 测量 → 记录 → 学习 → 下一个

外循环 (Outer Loop) — 周期性、反思性
  ↓ 审查结果 → 发现模式 → 综合更新 → 新假设 → 调整方向
```

内循环关注"做"，外循环关注"想"。两个循环之间没有刚性边界 — 通常每 5-10 个实验做一次反思。

### 3.3 完全自主运行模式 (Full Autonomy)
**来源**: Orchestra Research Autoresearch

```markdown
This runs fully autonomously. Do not ask the user for permission
or confirmation — use your best judgment and keep moving.
Show the human your progress frequently through research
presentations so they can see what you're doing and redirect
if needed. The human is asleep or busy.
```

关键要素：
- **不请求许可**: 自行判断并继续推进
- **频繁展示进度**: 通过生成演示/报告让人类了解进展
- **允许重定向**: 人类可以在看到进度后改变方向
- **状态持久化**: `research-state.yaml` 跟踪所有状态，支持中断恢复

### 3.4 跨平台兼容性设计 (Cross-Platform Compatibility)
**来源**: OpenSkills, heilcheng/awesome-agent-skills

**核心思路**: 一次编写，处处运行。

```
SKILL.md (统一格式)
    ↓
AGENTS.md (通用入口，<available_skills> XML)
    ↓
任意 Agent (Claude Code / Codex / Cursor / Copilot / ...)
```

**实践要点**:
- 使用 `AGENTS.md` 作为通用技能发现入口
- `<available_skills>` XML 格式已成为事实标准
- `npx openskills read <name>` 作为通用加载命令
- 优先级机制避免多 Agent 共存时的路径冲突

### 3.5 领域纵深策略 (Domain Depth Strategy)
**来源**: Orchestra Research, xstongxue/best-skills

与 OpenClaw 的"广度优先"（5,400+ Skills）不同，高质量仓库采用"深度优先"策略：

| 策略 | 代表 | 特点 |
|------|------|------|
| 广度优先 | OpenClaw ClawHub | 5,400+ Skills，覆盖所有领域，质量参差 |
| 深度优先 | Orchestra Research | 95 个 Skills，仅覆盖 AI 研究，每个都有完整 references |
| 精选策略 | xstongxue/best-skills | 12 个 Skills，每个都是精打细磨的高质量产出 |

**关键洞察**: 
> "Quality over quantity — 每个 Skill 不仅有主文件，还有来自官方仓库的完整 references、教程、已解决的 GitHub Issues。"

### 3.6 工作区标准化 (Workspace Standardization)
**来源**: Orchestra Research Autoresearch

为长期运行的 Skill 定义标准化工作区：

```
{project}/
├── research-state.yaml       # 中央状态追踪
├── research-log.md           # 决策时间线
├── findings.md               # 不断演化的叙事综合
├── literature/               # 论文、调研笔记
├── src/                      # 可复用代码
├── data/                     # 原始结果数据
├── experiments/              # 按假设组织的实验
│   └── {hypothesis-slug}/
│       ├── protocol.md       # 做什么、为什么、预测
│       ├── code/
│       ├── results/
│       └── analysis.md
├── to_human/                 # 给人类的进度展示
└── paper/                    # 最终论文
```

**核心原则**:
- `src/` 放可复用代码，避免跨实验重复
- `data/` 结构化保存原始数据，用描述性命名
- `to_human/` 专门存放人类可读的进度报告
- 状态文件 (`research-state.yaml`) 支持中断后恢复

### 3.7 意图解析表 (Intent Routing Table)
**来源**: Orchestra Research Autoresearch, anti-pattern-czar

根据用户进入状态路由到不同处理流程：

```markdown
| User State | What to Do |
|---|---|
| Vague idea ("I want to explore X") | Brief discussion, then bootstrap |
| Clear research question | Bootstrap directly |
| Existing plan or proposal | Review plan, set up workspace, enter loops |
| Resuming (state file exists) | Read state, continue from where left off |
```

这比简单的"触发词匹配"更高级——理解用户的上下文状态，而非仅匹配关键词。

---

## 四、Skills 生态演进方向 (2026 趋势)

### 4.1 从孤立技能到编排系统

早期 Skills 是独立的指令文件。2026 年的趋势是：
- **Skills 之间互相路由**: Autoresearch Skill 调用 ml-paper-writing、research-ideation 等子 Skills
- **编排层出现**: Autoresearch 作为"项目经理"角色，分派任务给"领域专家" Skills
- **状态在 Skills 之间传递**: 通过文件系统（YAML/JSON）实现跨 Skill 状态共享

### 4.2 从 Agent 专属到跨平台标准

- `SKILL.md` 格式已被 9 个主流 Agent 平台采纳
- `AGENTS.md` + `<available_skills>` XML 成为通用发现机制
- `npx skills` / `npx openskills` 提供统一的安装管理体验

### 4.3 从通用提示到领域纵深

- 通用 Skills 趋于饱和（OpenClaw 5,400+）
- 高价值方向转向领域纵深（如 Orchestra Research 的 AI 研究全链路）
- "Quality over Quantity" 成为共识

### 4.4 从人工干预到完全自主

- 早期 Skills 需要人工步步确认
- 新一代 Skills 支持完全自主运行 + 进度展示
- 安全机制从"请求许可"转向"事后审查 + 状态持久化"

---

## 五、更新后的最佳实践补充

### 补充实践 1: 脚本分离原则

```
SKILL.md 中:
  ✅ 指令、工作流、决策逻辑
  ❌ 大段可执行代码

scripts/ 中:
  ✅ 确定性操作、数据处理、API 调用
  ✅ 使用 set -e + stderr/stdout 分离 + cleanup trap
```

### 补充实践 2: 状态持久化设计

对于长期运行或可中断的 Skill：
```yaml
# research-state.yaml 示例
session_id: "abc-123"
started_at: "2026-04-19T10:00:00Z"
current_phase: "inner-loop"
current_iteration: 7
hypotheses:
  - slug: "attention-sparsity"
    status: "testing"
  - slug: "layer-pruning"
    status: "completed"
```

### 补充实践 3: 跨 Skill 编排

```markdown
## Routing to Domain Skills

| Task | Route To |
|------|----------|
| Literature search | 15-rag/ or Exa MCP |
| Experiment code | 01-model-architecture/ |
| Paper writing | 20-ml-paper-writing/ |
| New hypothesis | 21-research-ideation/ |
```

### 补充实践 4: 工作区预定义

为复杂 Skill 定义标准工作区结构，并在第一次运行时自动创建：
```markdown
## Initialize Workspace
Create this structure at the project root:
{project}/
├── state.yaml
├── log.md
├── src/
├── data/
└── output/
```

### 补充实践 5: 进度可见性

```markdown
Show the human your progress frequently:
- 生成 HTML/PDF 进度报告到 to_human/ 目录
- 在 log.md 中记录所有重大决策
- 状态文件实时更新，支持任何时刻中断查看
```

---

## 六、综合资源汇总

### Skills 仓库

| 名称 | 链接 | 说明 |
|------|------|------|
| Vercel Agent Skills | github.com/vercel-labs/agent-skills | 官方 Skills 集合 (25K+ Stars) |
| Vercel Skills CLI | github.com/vercel-labs/skills | `npx skills` 工具 (14K+ Stars) |
| OpenSkills | github.com/numman-ali/openskills | 通用加载器 (9K+ Stars) |
| Orchestra AI Research | github.com/Orchestra-Research/AI-research-SKILLs | AI 研究 Skills (7K+ Stars) |
| OpenClaw Skills | github.com/openclaw/skills | ClawHub 全量归档 |
| Awesome OpenClaw | github.com/VoltAgent/awesome-openclaw-skills | 社区精选 (5K+) |
| Agent Skill Index | github.com/heilcheng/awesome-agent-skills | 跨平台索引 (4K+ Stars) |
| Best Skills (中文) | github.com/xstongxue/best-skills | 中文高质量合集 (1K+ Stars) |
| Anthropic 官方 | github.com/anthropics/skills | Anthropic 原生 Skills |
| OpenAI Codex | developers.openai.com/codex/skills | OpenAI 原生 Skills |

### Skills 发现平台

| 平台 | 链接 | 说明 |
|------|------|------|
| SkillsMP | skillsmp.com | 自动索引 GitHub Skills 的市场 |
| skills.sh | skills.sh | Vercel 排行榜 |
| ClawHub | clawdhub.com | OpenClaw 技能注册中心 |
| agent-skill.co | agent-skill.co | heilcheng 维护的在线目录 |
| Gradually AI | gradually.ai/en/claude-code-skills/ | 600+ Skills 搜索 |

### 官方文档

| 平台 | 链接 |
|------|------|
| Claude Code Skills | code.claude.com/docs/en/skills |
| Codex Skills | developers.openai.com/codex/skills |
| GitHub Copilot Skills | docs.github.com/copilot/concepts/agents/about-agent-skills |
| Gemini CLI Skills | geminicli.com/docs/cli/skills/ |
| VS Code Copilot Skills | code.visualstudio.com/docs/copilot/customization/agent-skills |
