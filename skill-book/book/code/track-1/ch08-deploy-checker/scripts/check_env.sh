#!/usr/bin/env bash
# check_env.sh — 检查部署所需的环境变量
# stdout: JSON 检查结果
# stderr: 状态信息

set -e

echo "=== 环境变量检查 ===" >&2

PASS=0
FAIL=0
MISSING=""

# 检查 .env 文件是否存在
if [ -f .env ]; then
  echo "  ✓ .env 文件存在" >&2
  PASS=$((PASS + 1))
else
  echo "  ⚠ .env 文件不存在" >&2
fi

# 检查 .env.example 与 .env 的差异
if [ -f .env.example ]; then
  echo "  检查 .env.example 覆盖情况..." >&2
  while IFS= read -r line; do
    # 跳过注释和空行
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    VAR_NAME=$(echo "$line" | cut -d'=' -f1)
    if [ -f .env ] && grep -q "^${VAR_NAME}=" .env; then
      PASS=$((PASS + 1))
    else
      echo "  ✗ 缺失: $VAR_NAME" >&2
      FAIL=$((FAIL + 1))
      MISSING="${MISSING}\"${VAR_NAME}\","
    fi
  done < .env.example
fi

# 检查 .gitignore 是否保护敏感文件
GITIGNORE_OK=true
if [ -f .gitignore ]; then
  for pattern in ".env" "*.key" "*.pem" "credentials"; do
    if grep -q "$pattern" .gitignore 2>/dev/null; then
      PASS=$((PASS + 1))
    else
      echo "  ⚠ .gitignore 未包含 $pattern" >&2
      GITIGNORE_OK=false
    fi
  done
fi

# JSON 输出
cat <<EOF
{
  "check": "environment",
  "pass": $PASS,
  "fail": $FAIL,
  "missing_vars": [${MISSING%,}],
  "gitignore_protected": $GITIGNORE_OK,
  "status": "$([ $FAIL -eq 0 ] && echo 'PASS' || echo 'FAIL')"
}
EOF

echo "" >&2
echo "环境检查完成: $PASS 通过, $FAIL 失败" >&2
