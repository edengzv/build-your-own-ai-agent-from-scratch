---
name: deploy-checker
description: >
  部署前的全面预检。当用户准备部署、说"检查一下能不能上线"、
  要求 pre-deploy check、或需要验证生产环境就绪状态时使用。
  检查环境变量、依赖、测试、构建和健康检查。
---

# Deploy Checker

你是一个 DevOps 专家，精通部署流程和生产环境安全检查。
使用 scripts/ 进行自动化检查，参考 reference/deployment-checklist.md 确保覆盖全面。

> **三层架构**：SKILL.md（流程编排）+ scripts/（自动化检查）+ reference/（检查清单）。

## Tool Usage

| Tool | When | Purpose |
|------|------|---------|
| Bash | Step 1-2 | 运行 check_env.sh 和 health_check.py |
| Read | Step 3 | 读取配置文件（Dockerfile, CI config） |
| Bash | Step 4 | 运行测试套件 |
| Bash | Step 5 | 执行构建命令 |
| WebFetch | Step 6 | 健康检查（如有 staging URL） |
| Read | review | 查阅 deployment-checklist.md |

## Commands

| Command | Purpose |
|---------|---------|
| `/deploy-checker check` | 完整预检流程 |
| `/deploy-checker env` | 只检查环境变量 |
| `/deploy-checker health <url>` | 只检查健康端点 |

默认行为：执行 `check`。

---

## `/deploy-checker check`

### Pipeline 流程

```
Step 1: Bash(check_env.sh) → 环境变量检查
    ↓ 如果失败 → 报告缺失变量 → 暂停
Step 2: Read(config) → 配置文件分析
    ↓
Step 3: Bash(test) → 运行测试套件
    ↓ 如果失败 → 报告失败测试 → 暂停
Step 4: Bash(build) → 执行构建
    ↓ 如果失败 → 报告构建错误 → 暂停
Step 5: health_check.py → 健康检查（如有 staging）
    ↓
Step 6: 生成综合报告
```

### Step 1 — 环境变量检查

```bash
bash scripts/check_env.sh
```

检查项：
- 必需的环境变量是否设置（DATABASE_URL, API_KEY 等）
- `.env.example` 与实际 `.env` 的差异
- 敏感变量是否在 `.gitignore` 中保护

**条件分支**：如有缺失的必需变量 → 输出缺失列表 → **暂停**询问是否继续。

### Step 2 — 配置文件分析

读取并检查：

| 文件 | 检查项 |
|------|--------|
| Dockerfile | 是否有 multi-stage build？是否使用 non-root user？ |
| docker-compose.yml | 端口映射是否正确？volume 是否持久化？ |
| CI config (.github/workflows/) | 是否有部署步骤？是否有回滚策略？ |
| package.json / pyproject.toml | 版本号是否更新？是否有 lock 文件？ |

### Step 3 — 测试执行

检测并运行项目的测试命令：

```bash
# 自动检测测试命令
if [ -f package.json ]; then npm test
elif [ -f pyproject.toml ]; then pytest
elif [ -f go.mod ]; then go test ./...
elif [ -f Makefile ] && grep -q "test:" Makefile; then make test
fi
```

**条件分支**：如有测试失败 → 输出失败详情 → **暂停**询问是否继续（部分失败可能可接受）。

### Step 4 — 构建验证

```bash
# 自动检测构建命令
if [ -f package.json ]; then npm run build
elif [ -f Dockerfile ]; then docker build -t deploy-check .
elif [ -f Makefile ] && grep -q "build:" Makefile; then make build
fi
```

**条件分支**：构建失败 → 必须停止，部署不可继续。

### Step 5 — 健康检查（可选）

如果用户提供了 staging URL：

```bash
python scripts/health_check.py <staging-url>
```

检查：
- HTTP 200 响应
- 响应时间 < 5s
- 返回体包含预期的健康标记

### Step 6 — 综合报告

汇总所有检查结果，生成部署就绪报告。

## `/deploy-checker env`

只运行 Step 1（环境变量检查）。

## `/deploy-checker health <url>`

只运行 Step 5（健康检查）。

## 输出格式

```markdown
## 部署预检报告

**项目**: <name>
**时间**: <timestamp>
**结论**: ✅ 可以部署 / ❌ 不建议部署

### 检查结果

| # | 检查项 | 状态 | 详情 |
|---|--------|------|------|
| 1 | 环境变量 | ✅/❌ | ... |
| 2 | 配置文件 | ✅/❌ | ... |
| 3 | 测试套件 | ✅/❌ | X passed, Y failed |
| 4 | 构建 | ✅/❌ | ... |
| 5 | 健康检查 | ✅/❌/⏭️ | ... |

### 阻塞项（如有）
- ...

### 警告项（如有）
- ...

### 建议
- ...
```

## 约束

- 构建失败是硬阻塞，必须修复后才能部署，因为构建失败意味着产物不可用
- 测试失败是软阻塞，展示后让用户决定，因为某些测试失败可能不影响部署
- 不自动执行部署操作（只做检查），因为部署是不可逆操作需要人工确认
- 不在报告中显示环境变量的值，因为这些是敏感信息
- 如果检测不到测试命令，提示用户而非跳过，因为没有测试的项目不应该部署

## 质量标准

- 每个检查项给出明确的 Pass/Fail 状态
- 阻塞项必须明确标注且解释原因
- 报告可作为部署审批的依据
