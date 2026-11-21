#!/bin/bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only verification of a security or build invariant.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 验证 backend 完整登录链路（captcha -> Redis 取码 -> login）
NODE=172.18.0.5
PORT=30989
echo "=== 1) captcha ==="
RESP=$(curl -s -m 10 "http://${NODE}:${PORT}/captchaImage")
echo "captcha head: ${RESP:0:90}"
UUID=$(echo "$RESP" | sed -n 's/.*"uuid":"\([^"]*\)".*/\1/p')
echo "uuid=${UUID}"
echo "=== 2) read captcha code from WSL redis :6380 ==="
CODE=$(redis-cli -p 6379 get "captcha_codes:${UUID}" | tr -d '"')
echo "code=${CODE}"
echo "=== 3) login ==="
curl -s -m 15 -X POST "http://${NODE}:${PORT}/login" \
  -H 'Content-Type: application/json' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -d "{\"username\":\"admin\",\"password\":\"admin123\",\"code\":\"${CODE}\",\"uuid\":\"${UUID}\"}" \
  -w '\nHTTP:%{http_code}\n'
