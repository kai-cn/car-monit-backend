#!/usr/bin/env bash

# @description 历史脚本 manual-native-port.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash manual-native-port.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION

# 文件：manual-native-port.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

# Start the native binary with an explicit --server.port override and report the

# outcome, to separate "port 9902 conflict" from "startup blocked elsewhere".

set -u

BIN=${1:?binary}

PORT=${2:-18080}

SECS=${3:-50}

OUT=/mnt/d/work/runtime-logs/v3-ops/evidence/manual-native-start-$PORT.log



PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -n 1)

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$PASS"



cd "$(dirname "$BIN")" || exit 3

"$BIN" --server.port="$PORT" >"$OUT" 2>&1 &

PID=$!

BOUND=0

for i in $(seq 1 "$SECS"); do

  sleep 1

  if ! kill -0 "$PID" 2>/dev/null; then echo "process exited at ${i}s"; break; fi

  if ss -lnt 2>/dev/null | grep -q ":$PORT"; then BOUND=1; echo "bound $PORT at ${i}s"; break; fi

done

echo "bound=$BOUND rss_mb=$(( $(ps -o rss= -p "$PID" 2>/dev/null | tr -d ' ' || echo 0) / 1024 ))"

echo "=== markers ==="

grep -E "Started EcBusiness|Tomcat started|APPLICATION FAILED|Port .* was already in use|Netty started" "$OUT" | tail -n 6

kill -9 "$PID" 2>/dev/null || true

