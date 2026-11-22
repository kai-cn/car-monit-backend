#!/usr/bin/env bash

# @description 历史脚本 fix-cluster-env.sh：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash fix-cluster-env.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

echo "=== delete deployments for a clean env rebuild ==="

docker exec k3d-v3-server-0 kubectl delete deployment car-monit-backend car-monit-api 2>&1

echo "=== re-apply clean manifest (no CLUSTER_NODES) ==="

cat /mnt/d/work/runtime-logs/manifests-final.yaml | docker exec -i k3d-v3-server-0 kubectl apply -f - 2>&1 | grep -E 'created|configured|unchanged'

echo "=== new backend pod env REDIS ==="

sleep 15

docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-backend -- bash -c 'env | grep -i redis' 2>&1

