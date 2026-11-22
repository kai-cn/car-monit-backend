#!/usr/bin/env bash

# @description 历史脚本 28-recreate-sync.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash 28-recreate-sync.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION

# 文件：28-recreate-sync.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

set -u

REG=/mnt/d/work/runtime-logs/wsl-setup/k3d-registries.yaml

sed -i 's/\r$//' "$REG"

echo "=== deleting old cluster ==="

/usr/local/bin/k3d cluster delete v3

echo "=== creating cluster ==="

/usr/local/bin/k3d cluster create v3 \

  --servers 1 \

  --agents 2 \

  --image rancher/k3s:v1.35.5-k3s1 \

  --registry-config "$REG" \

  --k3s-arg '--disable=traefik@server:0' \

  --k3s-arg '--disable=metrics-server@server:0' \

  --port '6443:6443@loadbalancer' \

  --wait --timeout 6m

echo "CREATE_RC=$?"

echo "=== nodes ==="

docker exec k3d-v3-server-0 kubectl get nodes

echo "=== system pods ==="

docker exec k3d-v3-server-0 kubectl get pods -A

