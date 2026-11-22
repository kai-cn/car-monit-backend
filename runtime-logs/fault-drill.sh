#!/usr/bin/env bash

# @description 历史脚本 fault-drill.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash fault-drill.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

POD=$(docker exec k3d-v3-server-0 kubectl get pods -l app=car-monit-backend -o jsonpath='{.items[0].metadata.name}')

echo "=== 删除后端 Pod: $POD ==="

docker exec k3d-v3-server-0 kubectl delete pod "$POD"

echo "=== 等待自愈重建 (45s) ==="

sleep 45

docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide 2>&1 | grep -E 'NAME|api-|backend-'

echo "=== 自愈后验证码 ==="

bash /mnt/d/work/runtime-logs/captcha-check.sh

