#!/usr/bin/env bash

# @description 历史脚本 step10-cleanup.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash step10-cleanup.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

K="docker exec k3d-v3-server-0 kubectl"

echo "=== delete cluster test workloads ==="

$K delete deploy car-monit-api car-monit-backend --ignore-not-found

$K delete svc car-monit-api car-monit-backend --ignore-not-found

$K delete secret car-monit-cluster-secrets --ignore-not-found

sleep 5

echo "=== remaining pods ==="

$K get pods -A 2>&1 | head -12

echo "=== stop cluster-shared redis :6380 ==="

redis-cli -h 127.0.0.1 -p 6380 shutdown nosave >/dev/null 2>&1 || true

sleep 1

redis-cli -h 127.0.0.1 -p 6380 ping 2>&1 || echo "redis 6380 stopped"

echo "=== WSL memory after cleanup ==="

free -h | head -2

