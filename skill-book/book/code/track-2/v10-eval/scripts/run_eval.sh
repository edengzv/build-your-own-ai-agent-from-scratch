#!/usr/bin/env bash
# run_eval.sh — 运行 Skill 的触发测试和质量断言
# 用法: bash run_eval.sh <skill-directory>
# stdout: JSON 评测结果
# stderr: 状态信息

set -e

SKILL_DIR="${1:?用法: run_eval.sh <skill-directory>}"

if [ ! -d "$SKILL_DIR" ]; then
  echo "Error: 目录不存在: $SKILL_DIR" >&2
  exit 1
fi

SKILL_FILE="$SKILL_DIR/SKILL.md"
TRIGGER_FILE="$SKILL_DIR/trigger-tests.yaml"
ASSERT_FILE="$SKILL_DIR/output-assertions.yaml"

echo "=== Skill 评测 ===" >&2
echo "目录: $SKILL_DIR" >&2
echo "" >&2

# Phase 1: 结构验证
echo "--- Phase 1: 结构验证 ---" >&2
STRUCT_PASS=true
if [ -f "$SKILL_FILE" ]; then
  echo "  ✓ SKILL.md 存在" >&2
else
  echo "  ✗ SKILL.md 不存在" >&2
  STRUCT_PASS=false
fi

# Phase 2: 触发测试检查
echo "" >&2
echo "--- Phase 2: 触发测试 ---" >&2
TRIGGER_COUNT=0
if [ -f "$TRIGGER_FILE" ]; then
  POSITIVE=$(grep -c "should_trigger\|^  - " "$TRIGGER_FILE" 2>/dev/null || echo "0")
  echo "  ✓ trigger-tests.yaml 存在 ($POSITIVE 条测试)" >&2
  TRIGGER_COUNT=$POSITIVE
else
  echo "  ⚠ trigger-tests.yaml 不存在（建议生成）" >&2
fi

# Phase 3: 质量断言检查
echo "" >&2
echo "--- Phase 3: 质量断言 ---" >&2
ASSERT_COUNT=0
if [ -f "$ASSERT_FILE" ]; then
  ASSERTIONS=$(grep -c "type:" "$ASSERT_FILE" 2>/dev/null || echo "0")
  echo "  ✓ output-assertions.yaml 存在 ($ASSERTIONS 条断言)" >&2
  ASSERT_COUNT=$ASSERTIONS

  # 检查三层覆盖
  HAS_EXISTS=$(grep -c "exists\|contains" "$ASSERT_FILE" 2>/dev/null || echo "0")
  HAS_QUALITY=$(grep -c "format\|max_length\|pattern" "$ASSERT_FILE" 2>/dev/null || echo "0")
  HAS_SAFETY=$(grep -c "safety\|forbidden\|not_contains" "$ASSERT_FILE" 2>/dev/null || echo "0")

  echo "  三层覆盖: 存在性=$HAS_EXISTS 质量=$HAS_QUALITY 安全性=$HAS_SAFETY" >&2
else
  echo "  ⚠ output-assertions.yaml 不存在（建议生成）" >&2
fi

# Phase 4: Description 质量检查
echo "" >&2
echo "--- Phase 4: Description 分析 ---" >&2
if [ -f "$SKILL_FILE" ]; then
  # 提取 description（简化版，只检查长度）
  DESC_LINES=$(sed -n '/^description:/,/^---/p' "$SKILL_FILE" | wc -l | tr -d ' ')
  echo "  description 行数: $DESC_LINES" >&2
  if [ "$DESC_LINES" -ge 2 ]; then
    echo "  ✓ description 长度充足" >&2
  else
    echo "  ⚠ description 可能过短（建议 50-150 字）" >&2
  fi
fi

# 输出 JSON
echo "" >&2
cat <<EOF
{
  "skill_dir": "$SKILL_DIR",
  "structure_valid": $STRUCT_PASS,
  "trigger_tests": $TRIGGER_COUNT,
  "assertions": $ASSERT_COUNT,
  "recommendations": [
    $([ $TRIGGER_COUNT -eq 0 ] && echo '"生成 trigger-tests.yaml (5正+5负)",' || echo '')
    $([ $ASSERT_COUNT -lt 3 ] && echo '"补充质量断言至少 3 条 (存在性+质量+安全性)",' || echo '')
    "运行实际触发测试验证 description 匹配率"
  ]
}
EOF

echo "" >&2
echo "评测完成" >&2
