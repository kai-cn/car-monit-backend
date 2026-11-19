#!/usr/bin/env bash
# Probe: start the native binary with Druid filters turned off, to confirm the
# NPE at DruidDataSource.setConnectProperties:640 (filter.configFromProperties).
set -u
BIN=${1:?binary}
PORT=${2:-19902}
SECS=${3:-45}
OUT=/mnt/d/work/runtime-logs/v3-ops/evidence/druid-nofilter-$PORT.log

PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -n 1)
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$PASS"
# 关掉 druid filters，并把 connectProperties 置空
export SPRING_DATASOURCE_DYNAMIC_DRUID_FILTERS=""
export SPRING_DATASOURCE_DYNAMIC_DRUID_CONNECTIONPROPERTIES=""

cd "$(dirname "$BIN")" || exit 3
"$BIN" --server.port="$PORT" >"$OUT" 2>&1 &
PID=$!
for i in $(seq 1 "$SECS"); do
  sleep 1
  if ! kill -0 "$PID" 2>/dev/null; then echo "exited at ${i}s"; break; fi
  if grep -q "Started EcBusinessApiApplication" "$OUT" 2>/dev/null; then echo "STARTED at ${i}s"; break; fi
done
echo "=== markers ==="
grep -E "Started EcBusiness|APPLICATION FAILED|Caused by: java.lang.NullPointer|BindException|Tomcat started" "$OUT" | tail -n 8
kill -9 "$PID" 2>/dev/null || true
echo "log: $OUT"
