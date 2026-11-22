#!/usr/bin/env bash

# @description 历史脚本 hikari-native-start.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash hikari-native-start.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION

# 文件：hikari-native-start.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

# Start the native binary with the dynamic datasource type forced to Hikari, to

# bypass the Druid creator NPE seen under Spring Boot 3 native.

set -u

BIN=${1:?binary}

PORT=${2:-19902}

SECS=${3:-60}

OUT=/mnt/d/work/runtime-logs/v3-ops/evidence/hikari-native-start-$PORT.log



PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -n 1)

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$PASS"

export SPRING_DATASOURCE_DYNAMIC_TYPE=com.zaxxer.hikari.HikariDataSource



cd "$(dirname "$BIN")" || exit 3

"$BIN" --server.port="$PORT" >"$OUT" 2>&1 &

PID=$!

BOUND=0

for i in $(seq 1 "$SECS"); do

  sleep 1

  if ! kill -0 "$PID" 2>/dev/null; then echo "exited at ${i}s"; break; fi

  if grep -q "Started EcBusinessApiApplication" "$OUT" 2>/dev/null; then BOUND=2; echo "started at ${i}s"; break; fi

  if grep -qi ":$PORT " /proc/net/tcp /proc/net/tcp6 2>/dev/null; then BOUND=1; echo "bound at ${i}s"; break; fi

done

echo "state=$BOUND"

echo "=== markers ==="

grep -E "Started EcBusiness|Tomcat started|APPLICATION FAILED|Caused by|HikariPool" "$OUT" | tail -n 8

kill -9 "$PID" 2>/dev/null || true

echo "log: $OUT"

