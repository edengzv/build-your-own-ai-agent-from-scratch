#!/usr/bin/env bash
# validate_skill.sh — v10 版本，同 v09
set -e
SKILL_PATH="${1:?用法: validate_skill.sh <path-to-SKILL.md>}"
[ ! -f "$SKILL_PATH" ] && echo "Error: 文件不存在: $SKILL_PATH" >&2 && exit 1
echo "正在验证: $SKILL_PATH" >&2
PASS=0; FAIL=0; WARNINGS=""

head -1 "$SKILL_PATH" | grep -q "^---$" && { echo "  ✓ Frontmatter" >&2; PASS=$((PASS+1)); } || { echo "  ✗ Frontmatter" >&2; FAIL=$((FAIL+1)); }
grep -q "^name:" "$SKILL_PATH" && { echo "  ✓ name" >&2; PASS=$((PASS+1)); } || { echo "  ✗ name" >&2; FAIL=$((FAIL+1)); }
grep -q "^description:" "$SKILL_PATH" && { echo "  ✓ description" >&2; PASS=$((PASS+1)); } || { echo "  ✗ description" >&2; FAIL=$((FAIL+1)); }
grep -qE "^##.*(执行步骤|Pass [0-9])" "$SKILL_PATH" && { echo "  ✓ 步骤" >&2; PASS=$((PASS+1)); } || { echo "  ✗ 步骤" >&2; FAIL=$((FAIL+1)); }
grep -qE "^##.*输出格式" "$SKILL_PATH" && { echo "  ✓ 输出格式" >&2; PASS=$((PASS+1)); } || { echo "  ✗ 输出格式" >&2; FAIL=$((FAIL+1)); }
grep -qE "^##.*约束" "$SKILL_PATH" && { echo "  ✓ 约束" >&2; PASS=$((PASS+1)); } || { echo "  ✗ 约束" >&2; FAIL=$((FAIL+1)); }
grep -qE "^##.*Tool Usage" "$SKILL_PATH" && { echo "  ✓ Tool Usage" >&2; PASS=$((PASS+1)); } || { WARNINGS="${WARNINGS}\"tool_usage\": false,"; }
grep -qE "^##.*Guardrails" "$SKILL_PATH" && { echo "  ✓ Guardrails" >&2; PASS=$((PASS+1)); } || { WARNINGS="${WARNINGS}\"guardrails\": false,"; }

LINES=$(wc -l < "$SKILL_PATH" | tr -d ' ')
[ "$LINES" -gt 300 ] && WARNINGS="${WARNINGS}\"line_warning\": \"$LINES > 300\"," || PASS=$((PASS+1))

echo "{\"file\":\"$SKILL_PATH\",\"lines\":$LINES,\"pass\":$PASS,\"fail\":$FAIL,$WARNINGS\"status\":\"$([ $FAIL -eq 0 ] && echo PASS || echo FAIL)\"}"
echo "验证完成: $PASS 通过, $FAIL 失败" >&2
exit $FAIL
