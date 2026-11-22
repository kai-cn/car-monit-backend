#!/usr/bin/env bash

# @description 历史脚本 26-recreate-cluster-3g.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash 26-recreate-cluster-3g.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION

# 文件：26-recreate-cluster-3g.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

set -u

LOG=/tmp/k3d-recreate.log

REG=/mnt/d/work/runtime-logs/wsl-setup/k3d-registries.yaml

echo "start $(date -Is)" > "$LOG"

sed -i 's/\r$//' "$REG"

/usr/local/bin/k3d cluster delete v3 >> "$LOG" 2>&1

sleep 3

/usr/local/bin/k3d cluster create v3 \

  --servers 1 \

  --agents 2 \

  --image rancher/k3s:v1.35.5-k3s1 \

  --registry-config "$REG" \

  --k3s-arg '--disable=traefik@server:0' \

  --k3s-arg '--disable=metrics-server@server:0' \

  --port '6443:6443@loadbalancer' \

  --wait --timeout 6m >> "$LOG" 2>&1

echo "CREATE_RC=$? $(date -Is)" >> "$LOG"

docker exec k3d-v3-server-0 kubectl get nodes >> "$LOG" 2>&1

docker exec k3d-v3-server-0 kubectl get pods -A >> "$LOG" 2>&1

echo "done" >> "$LOG"

touch /tmp/k3d-recreate.done

