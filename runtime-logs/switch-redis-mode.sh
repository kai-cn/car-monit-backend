#!/usr/bin/env bash

# @description 历史脚本 switch-redis-mode.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash switch-redis-mode.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 在 单节点(6379) 与 6 节点 Cluster(7000-7005) 之间切换 Redis 模式。

# 可靠做法：先删除 Deployment，再按对应清单重建——避免 `kubectl set env --remove`

# 因三方合并残留 CLUSTER_NODES/HOST 键（曾导致 backend 误连已停的 cluster）。

# 用法: sudo bash switch-redis-mode.sh single|cluster

set -euo pipefail

MODE="${1:-single}"

[ "$MODE" = "single" ] || [ "$MODE" = "cluster" ] || { echo "usage: $0 single|cluster" >&2; exit 1; }

KCTL="docker exec k3d-v3-server-0 kubectl"

PORTS="7000 7001 7002 7003 7004 7005"



if [ "$MODE" = "single" ]; then

  echo ">>> 切换到 单节点 (6379)"

  for p in $PORTS; do systemctl stop redis-cluster@$p 2>/dev/null || true; done

  systemctl start redis-single

  sleep 2; redis-cli -p 6379 ping

  MANIFEST=/mnt/d/work/runtime-logs/manifests-final.yaml

else

  echo ">>> 切换到 Cluster (7000-7005)"

  systemctl stop redis-single 2>/dev/null || true

  for p in $PORTS; do systemctl start redis-cluster@$p; done

  sleep 3; redis-cli -p 7000 cluster info | grep cluster_state

  MANIFEST=/mnt/d/work/runtime-logs/manifests-cluster.yaml

fi



echo ">>> 删除并按 $MODE 清单重建 Deployment"

$KCTL delete deployment car-monit-backend car-monit-api

cat "$MANIFEST" | docker exec -i k3d-v3-server-0 kubectl apply -f -

echo ">>> 已切换到 $MODE；等待 Pod Ready 后即可验证"

