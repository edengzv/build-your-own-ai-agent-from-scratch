#!/usr/bin/env bash
# validate_skill.sh — 验证 SKILL.md 的结构完整性
# 用法: bash validate_skill.sh <path-to-SKILL.md>
# stdout: JSON 验证结果
# stderr: 状态信息

set -e

SKILL_PATH="${1:?用法: validate_skill.sh <path-to-SKILL.md>}"

if [ ! -f "$SKILL_PATH" ]; then
  echo "Error: 文件不存在: $SKILL_PATH" >&2
  exit 1
fi

echo "正在验证: $SKILL_PATH" >&2

PASS=0
FAIL=0
WARNINGS=""

# 检查 1: YAML Frontmatter
if head -1 "$SKILL_PATH" | grep -q "^---$"; then
  echo "  ✓ YAML Frontmatter 存在" >&2
  PASS=$((PASS + 1))
else
  echo "  ✗ 缺少 YAML Frontmatter" >&2
  FAIL=$((FAIL + 1))
fi

# 检查 2: name 字段 (kebab-case)
if grep -q "^name:" "$SKILL_PATH"; then
  NAME=$(grep "^name:" "$SKILL_PATH" | head -1 | sed 's/name: *//')
  if echo "$NAME" | grep -qE "^[a-z][a-z0-9-]*$"; then
    echo "  ✓ name: $NAME (kebab-case)" >&2
    PASS=$((PASS + 1))
  else
    echo "  ✗ name 不是 kebab-case: $NAME" >&2
    FAIL=$((FAIL + 1))
  fi
else
  echo "  ✗ 缺少 name 字段" >&2
  FAIL=$((FAIL + 1))
fi

# 检查 3: description 字段
if grep -q "^description:" "$SKILL_PATH"; then
  echo "  ✓ description 字段存在" >&2
  PASS=$((PASS + 1))
else
  echo "  ✗ 缺少 description 字段" >&2
  FAIL=$((FAIL + 1))
fi

# 检查 4: 执行步骤或 Pass 结构
if grep -qE "^##.*(执行步骤|Pass [0-9])" "$SKILL_PATH"; then
  echo "  ✓ 包含执行步骤或 Multi-Pass 结构" >&2
  PASS=$((PASS + 1))
else
  echo "  ✗ 缺少执行步骤" >&2
  FAIL=$((FAIL + 1))
fi

# 检查 5: 输出格式
if grep -qE "^##.*输出格式" "$SKILL_PATH"; then
  echo "  ✓ 包含输出格式说明" >&2
  PASS=$((PASS + 1))
else
  echo "  ✗ 缺少输出格式说明" >&2
  FAIL=$((FAIL + 1))
fi

# 检查 6: 约束
if grep -qE "^##.*约束" "$SKILL_PATH"; then
  echo "  ✓ 包含约束条件" >&2
  PASS=$((PASS + 1))
else
  echo "  ✗ 缺少约束条件" >&2
  FAIL=$((FAIL + 1))
fi

# 检查 7: Tool Usage 表
if grep -qE "^##.*Tool Usage" "$SKILL_PATH"; then
  echo "  ✓ 包含 Tool Usage 表" >&2
  PASS=$((PASS + 1))
else
  echo "  ⚠ 缺少 Tool Usage 表（可选但推荐）" >&2
  WARNINGS="${WARNINGS}\"tool_usage_warning\": \"no Tool Usage table found\","
fi

# 检查 8: Guardrails (v09 新增)
if grep -qE "^##.*Guardrails" "$SKILL_PATH"; then
  echo "  ✓ 包含 Guardrails" >&2
  PASS=$((PASS + 1))
else
  echo "  ⚠ 缺少 Guardrails 段（可选但推荐）" >&2
  WARNINGS="${WARNINGS}\"guardrails_warning\": \"no Guardrails section found\","
fi

# 检查 9: 反模式检测 — 模糊约束
if grep -qE "(合适的|恰当的|必要时|适当)" "$SKILL_PATH"; then
  echo "  ⚠ 疑似模糊约束（包含'合适的/恰当的/必要时/适当'）" >&2
  WARNINGS="${WARNINGS}\"vague_constraint_warning\": true,"
fi

# 检查 10: 行数
LINES=$(wc -l < "$SKILL_PATH" | tr -d ' ')
if [ "$LINES" -gt 300 ]; then
  echo "  ⚠ 行数偏多: ${LINES} 行（建议 < 300）" >&2
  WARNINGS="${WARNINGS}\"line_count_warning\": \"${LINES} lines exceeds recommended 300\","
elif [ "$LINES" -lt 10 ]; then
  echo "  ⚠ 行数过少: ${LINES} 行（可能不完整）" >&2
  WARNINGS="${WARNINGS}\"line_count_warning\": \"${LINES} lines may be incomplete\","
else
  echo "  ✓ 行数合理: ${LINES} 行" >&2
  PASS=$((PASS + 1))
fi

# 输出 JSON
cat <<EOF
{
  "file": "$SKILL_PATH",
  "lines": $LINES,
  "pass": $PASS,
  "fail": $FAIL,
  $WARNINGS
  "status": "$([ $FAIL -eq 0 ] && echo 'PASS' || echo 'FAIL')"
}
EOF

echo "" >&2
echo "验证完成: $PASS 通过, $FAIL 失败" >&2
exit $FAIL
