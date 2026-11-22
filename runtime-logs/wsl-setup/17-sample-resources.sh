#!/usr/bin/env bash

# @description 历史脚本 17-sample-resources.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash 17-sample-resources.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程；Maven 与对应 JDK
# LEGACY-SCRIPT-ANNOTATION

# 文件：17-sample-resources.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

# 采样 WSL2 内内存 / 容器 / 构建进程占用

# 用法: 17-sample-resources.sh <duration_seconds> <interval_seconds>

set -u

DUR=${1:-300}

INT=${2:-3}

OUT=/tmp/resource-samples.log

: > "$OUT"

END=$(( $(date +%s) + DUR ))

while [ "$(date +%s)" -lt "$END" ]; do

  TS=$(date +%H:%M:%S)

  MEM=$(free -m | awk '/^Mem:/ {printf "total=%s used=%s avail=%s", $2,$3,$7}')

  SWAP=$(free -m | awk '/^Swap:/ {printf "swap_used=%s", $3}')

  PROC=$(ps -eo rss,comm | awk '/Runner.Listener|run-helper|java|mvn|k3d|containerd/ {s+=$1} END {printf "%.0f", s/1024}')

  CONTAINERS=$(docker stats --no-stream --format '{{.Name}}:{{.MemUsage}}' 2>/dev/null | tr '\n' ',')

  echo "$TS | $MEM | $SWAP | proc_mb=$PROC | $CONTAINERS" >> "$OUT"

  sleep "$INT"

done

echo "DONE $(date +%H:%M:%S)" >> "$OUT"

touch /tmp/resource-samples.done

