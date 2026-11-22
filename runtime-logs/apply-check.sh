#!/usr/bin/env bash

# @description 历史脚本 apply-check.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash apply-check.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Apply a generated configuration to local or remote branches.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

echo "=== kubectl apply dry-run ==="

docker exec -i k3d-v3-server-0 kubectl apply --dry-run=client -f - < /mnt/d/work/runtime-logs/manifests-final.yaml 2>&1 | head -20

echo "=== file head ==="

head -8 /mnt/d/work/runtime-logs/manifests-final.yaml

echo "=== deployments ==="

docker exec k3d-v3-server-0 kubectl get deploy 2>&1 | head -12

