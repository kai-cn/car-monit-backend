#!/usr/bin/env bash

# @description 历史脚本 12-fix-registries.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash 12-fix-registries.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION

# 文件：12-fix-registries.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

set -u

LOG=/tmp/k3d-registries.log

echo "start $(date -Is)" > "$LOG"

cp /mnt/d/work/runtime-logs/wsl-setup/k3d-registries.yaml /tmp/registries.yaml

sed -i 's/\r$//' /tmp/registries.yaml

for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do

  docker exec "$n" mkdir -p /etc/rancher/k3s

  docker cp /tmp/registries.yaml "$n":/etc/rancher/k3s/registries.yaml

  echo "copied to $n" >> "$LOG"

done

for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do

  docker restart "$n" >> "$LOG" 2>&1

  echo "restarted $n" >> "$LOG"

done

echo "restart done $(date -Is)" >> "$LOG"

sleep 75

docker exec k3d-v3-server-0 kubectl get nodes >> "$LOG" 2>&1

docker exec k3d-v3-server-0 kubectl get pods -A >> "$LOG" 2>&1

echo "done $(date -Is)" >> "$LOG"

touch /tmp/k3d-registries.done

