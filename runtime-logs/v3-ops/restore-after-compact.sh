#!/usr/bin/env bash

# @description 历史脚本 restore-after-compact.sh：恢复工作树、提交元数据或容器状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash restore-after-compact.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Verify the new .wslconfig quota took effect after `wsl --shutdown`,

# then restore only the minimum services needed for native-image A/B testing.

set -uo pipefail

echo "################ RESTORE / VERIFY $(date -Is) ################"

echo "==== quota verification ===="

echo "nproc=$(nproc)"

free -m | head -2

echo "expected after 4GB/2cpu: Mem.total ~= 3944 MB, nproc = 2"

echo "==== systemd / docker ===="

systemctl is-active docker 2>&1

echo "==== containers ===="

docker ps -a --format 'table {{.Names}}\t{{.Status}}' 2>&1

echo "==== start DB / middleware (restart-policy independent) ===="

for c in mysql_wsl opengauss es-wsl kafka-wsl; do

  st=$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || echo absent)

  if [ "$st" != running ]; then

    echo "-- start $c (was $st)"

    docker start "$c" 2>&1 | head -2

  else

    echo "-- $c already running"

  fi

done

echo "==== re-apply measured DB memory limits ===="

bash /mnt/d/work/runtime-logs/set-db-memory-limits.sh 2>&1 | head -10

echo "==== standalone units (keep ONE mode active) ===="

for u in car-monit-api.service car-monit-backend.service; do

  printf "  %-32s active=%s enabled=%s\n" "$u" "$(systemctl is-active "$u" 2>/dev/null)" "$(systemctl is-enabled "$u" 2>/dev/null)"

done

echo "==== k3d nodes (should stay stopped) ===="

for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1 k3d-v3-serverlb; do

  printf "  %-24s %s\n" "$n" "$(docker inspect -f '{{.State.Status}}' "$n" 2>/dev/null || echo absent)"

done

echo "==== final memory ===="

free -m | head -2

echo "################ END ################"

