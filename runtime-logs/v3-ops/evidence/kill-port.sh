#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：kill-port.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
# Kill any leftover car-monit native/JVM process holding the given port.
set -u
PORT=${1:-9902}
PIDS=$(ss -lntp 2>/dev/null | awk -v p=":$PORT" '$4 ~ p {print $NF}' | sed -E 's/.*pid=([0-9]+).*/\1/' | sort -u)
if [ -z "${PIDS}" ]; then
  echo "no listener on $PORT"
else
  echo "killing: $PIDS"
  for pid in $PIDS; do kill -9 "$pid" 2>/dev/null || true; done
fi
sleep 1
ss -lntp 2>/dev/null | grep -c ":$PORT" || true
echo "done"
