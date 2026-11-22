#!/usr/bin/env bash

# @description 历史脚本 check-now.sh：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash check-now.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

echo "=== pods ==="

docker exec k3d-v3-server-0 kubectl get pods -o wide | grep car-monit

echo "=== backend log tail ==="

docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=8 2>&1 | tail -8

echo "=== NodePort captcha on all nodes ==="

for ip in 172.18.0.2 172.18.0.3 172.18.0.4; do

  printf '%s: ' "$ip"

  curl -s -o /dev/null -w '%{http_code}\n' -m 10 "http://$ip:30989/captchaImage"

done

echo "=== readiness from agent-0 node to backend ClusterIP ==="

docker exec k3d-v3-agent-0 wget -S -T 8 -O /dev/null http://10.43.173.187:9989/captchaImage 2>&1 | head -6

