#!/usr/bin/env bash

# @description 历史脚本 resp-test.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash resp-test.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

echo "=== pod RESP PING to 172.18.0.1:6379 (expect +PONG) ==="

docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-backend -- bash -c 'exec 3<>/dev/tcp/172.18.0.1/6379; printf "*1\r\n\$4\r\nPING\r\n" >&3; timeout 5 head -c 24 <&3; echo " <END>"' 2>&1

echo "=== pod env REDIS ==="

docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-backend -- bash -c 'env | grep -i redis' 2>&1

