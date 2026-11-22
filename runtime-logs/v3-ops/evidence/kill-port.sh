#!/usr/bin/env bash
# @description 历史脚本 kill-port.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash kill-port.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
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
