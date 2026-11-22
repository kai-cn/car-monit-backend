#!/usr/bin/env bash

# @description 历史脚本 cap-inspect.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash cap-inspect.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

curl -s -m 15 -D /tmp/cap.headers http://172.18.0.2:30989/captchaImage -o /tmp/cap.body

echo "=== headers ==="

head -12 /tmp/cap.headers

echo "=== body size / first 300 ==="

wc -c /tmp/cap.body

head -c 300 /tmp/cap.body

echo

echo "=== jq ==="

jq -r .uuid /tmp/cap.body 2>&1 | head -3

echo "=== backend pod status ==="

docker exec k3d-v3-server-0 kubectl get pods -l app=car-monit-backend -o wide

