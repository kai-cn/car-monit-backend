#!/usr/bin/env bash

# @description 历史脚本 step20-final-rollout.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash step20-final-rollout.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

K="docker exec k3d-v3-server-0 kubectl"

echo "=== re-import final slim images ==="

k3d image import car-monit-api:slim car-monit-backend:slim -c v3 2>&1 | tail -2

echo "=== rollout restart ==="

$K rollout restart deploy/car-monit-api deploy/car-monit-backend

for i in $(seq 1 24); do

  sleep 10

  d=$($K get deploy car-monit-api car-monit-backend --no-headers 2>/dev/null)

  echo "poll $i: $(echo "$d" | tr '\n' ' ')"

  ra=$(echo "$d" | awk '{s+=$2} END{print s}')

  [ "${ra:-0}" = "6" ] && { echo "3+3 READY"; break; }

done

echo "=== pods ==="

$K get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide

echo "=== log level distribution (should be ERROR only) ==="

for app in car-monit-api car-monit-backend; do

  logs=$($K logs deploy/"$app" --tail=200 2>/dev/null)

  total=$(echo "$logs" | wc -l)

  errs=$(echo "$logs" | grep -c 'ERROR' || true)

  noise=$(echo "$logs" | grep -cE 'INFO|DEBUG|TRACE|Consume Time|Execute SQL|\|-INFO' || true)

  echo "$app: lines=$total error_lines=$errs non_error_lines=$noise"

  echo "$logs" | head -5

done

