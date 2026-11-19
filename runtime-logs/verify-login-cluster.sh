#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only verification of a security or build invariant.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Cluster 模式下验证登录链路：从 7000 集群读取验证码
NODE=172.18.0.5
PORT=30989
RESP=$(curl -s -m 10 "http://${NODE}:${PORT}/captchaImage")
UUID=$(echo "$RESP" | sed -n 's/.*"uuid":"\([^"]*\)".*/\1/p')
echo "uuid=$UUID"
CODE=$(redis-cli -c -p 7000 get "captcha_codes:${UUID}" | tr -d '"')
echo "code=$CODE"
curl -s -m 15 -X POST "http://${NODE}:${PORT}/login" \
  -H 'Content-Type: application/json' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -d "{\"username\":\"admin\",\"password\":\"admin123\",\"code\":\"${CODE}\",\"uuid\":\"${UUID}\"}" \
  -w '\nHTTP:%{http_code}\n'
