#!/usr/bin/env bash

# @description 历史脚本 25-restart-cluster.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash 25-restart-cluster.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION

# 文件：25-restart-cluster.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

set -u

LOG=/tmp/cluster-restart.log

echo "start $(date -Is)" > "$LOG"

/usr/local/bin/k3d cluster stop v3 >> "$LOG" 2>&1

sleep 5

/usr/local/bin/k3d cluster start v3 --wait --timeout 5m >> "$LOG" 2>&1

echo "START_RC=$?" >> "$LOG"

sleep 15

docker exec k3d-v3-server-0 kubectl get nodes >> "$LOG" 2>&1

echo "done $(date -Is)" >> "$LOG"

touch /tmp/cluster-restart.done

