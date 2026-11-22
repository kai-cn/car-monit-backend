#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：manual-native-start.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
# Manual single-shot start: run the native binary for N seconds, report whether it
# bound the port and what the log says. No probing races.
set -u
BIN=${1:?binary}
PORT=${2:-9902}
SECS=${3:-40}
OUT=${4:-/mnt/d/work/runtime-logs/v3-ops/evidence/manual-native-start.log}

PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -n 1)
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$PASS"

echo "port_before: $(ss -lnt 2>/dev/null | grep -c ":$PORT")"
cd "$(dirname "$BIN")" || exit 3
"$BIN" >"$OUT" 2>&1 &
PID=$!
echo "pid=$PID starting, waiting ${SECS}s"
for i in $(seq 1 "$SECS"); do
  sleep 1
  if ! kill -0 "$PID" 2>/dev/null; then echo "exited at ${i}s"; break; fi
done
echo "port_after : $(ss -lnt 2>/dev/null | grep -c ":$PORT")"
echo "alive      : $(kill -0 "$PID" 2>/dev/null && echo yes || echo no)"
if kill -0 "$PID" 2>/dev/null; then
  echo "rss_mb     : $(( $(ps -o rss= -p "$PID" | tr -d ' ') / 1024 ))"
fi
echo "=== log tail ==="
tail -n 15 "$OUT"
kill -9 "$PID" 2>/dev/null || true
