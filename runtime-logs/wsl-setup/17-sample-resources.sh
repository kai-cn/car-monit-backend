#!/usr/bin/env bash
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
