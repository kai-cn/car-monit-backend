#!/usr/bin/env bash

# @description 历史脚本 verify-login-cluster.sh：验证配置、构建或安全不变量；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash verify-login-cluster.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
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

