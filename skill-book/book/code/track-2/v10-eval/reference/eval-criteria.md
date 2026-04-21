# 评测标准参考

> 本文件供 Agent 在设计测试用例和质量断言时查阅。

## 三层断言体系

Skill 输出质量通过三层断言验证：

### Layer 1: 存在性断言（Existence）

验证输出中**必须包含**的元素。

```yaml
- type: contains
  target: "feat|fix|refactor"
  description: 输出包含有效的 commit type
```

典型检查：
- 必要字段是否存在
- 必要格式标记是否出现
- 关键关键词是否包含

### Layer 2: 质量断言（Quality）

验证输出的**格式和内容质量**。

```yaml
- type: format
  pattern: "^(feat|fix)\\(.+\\): .{1,50}$"
  description: 符合 Conventional Commits 格式

- type: max_length
  target: 50
  scope: first_line
  description: subject 行不超过 50 字符
```

典型检查：
- 格式是否符合规范
- 长度是否在范围内
- 结构是否完整

### Layer 3: 安全性断言（Safety）

验证输出**不包含**不当内容。

```yaml
- type: not_contains
  target: "TODO|FIXME|待补充"
  description: 不包含占位符

- type: forbidden
  target: "password|secret|token"
  scope: output
  description: 不泄露敏感信息
```

典型检查：
- 不包含占位符
- 不泄露敏感信息
- 不包含有害建议

## 触发测试设计

### 正触发用例（5 条最低）

| 类型 | 说明 | 示例 |
|------|------|------|
| 精确匹配 | 用户直接说出 Skill 名称 | "帮我写 commit message" |
| 间接表述 | 用户描述任务但不说名称 | "提交这些改动" |
| 英文变体 | 英文表述 | "generate a commit msg" |
| 上下文触发 | 在特定上下文中 | "我 git add 完了" |
| 简略表述 | 极简请求 | "commit" |

### 负触发用例（5 条最低）

| 类型 | 说明 | 示例 |
|------|------|------|
| 相似但不同 | 相近任务但不是 | "帮我写 README" |
| 知识问答 | 问"是什么"而非"做什么" | "什么是 git rebase" |
| 不同领域 | 完全不同的任务 | "部署到生产环境" |
| 部分匹配 | 包含关键词但意图不同 | "解释 commit 规范" |
| 模糊请求 | 不够具体 | "帮我处理代码" |

## Description 优化循环

如果触发测试正确率 < 80%：

1. 分析失败用例 → 找出未覆盖的表述模式
2. 在 description 中添加对应的 When 子句或 Keywords
3. 重新运行触发测试
4. 重复直到 ≥ 80%

> 注意：不要为了提高正触发率而过度放宽 description，这会导致误触发。
> 目标是精准触发（precision）和充分触发（recall）的平衡。
