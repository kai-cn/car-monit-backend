#!/usr/bin/env bash

# @description 历史脚本 step7-scale.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash step7-scale.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

: "${CM_TOKEN:?}"

K="docker exec k3d-v3-server-0 kubectl"

echo "=== scale to 3 replicas each ==="

docker exec k3d-v3-server-0 kubectl scale deploy/car-monit-api --replicas=3

docker exec k3d-v3-server-0 kubectl scale deploy/car-monit-backend --replicas=3

echo "=== wait up to 300s ==="

for i in $(seq 1 30); do

  sleep 10

  d=$($K get deploy car-monit-api car-monit-backend --no-headers 2>/dev/null)

  p=$($K get pods -l 'app in (car-monit-api,car-monit-backend)' --no-headers 2>/dev/null)

  restarts=$(echo "$p" | awk '{s+=$4} END{print s}')

  echo "poll $i: $(echo "$d" | tr '\n' ' ') | restarts=${restarts:-0}"

  r=$(echo "$d" | awk '{s+=$3} END{print s}')

  w=$(echo "$d" | awk '{s+=$2} END{print s}')

  [ "${r:-0}" = "6" ] && [ "${w:-0}" = "6" ] && { echo "ALL 3+3 READY"; break; }

done

echo "=== pods / distribution ==="

$K get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide

echo "=== endpoints ==="

$K get endpoints car-monit-api car-monit-backend

echo "=== per-pod memory (crictl) ==="

for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do

  docker exec "$n" crictl stats -o json 2>/dev/null | jq -r '.stats[]? | select(.attributes.metadata.name | test("backend|api")) | [.attributes.metadata.name, ((.memory.workingSetBytes.value // 0) / 1048576 | floor | tostring)] | @tsv' 2>/dev/null | sort | head -8

done

echo "=== NodePort repeated requests ==="

for i in $(seq 1 12); do

  curl -s -o /dev/null -w '%{http_code} ' -m 15 -H "X-Internal-Token: $CM_TOKEN" 'http://172.18.0.2:30902/api/v3/es/readiness'

done

echo

echo "=== direct pod-IP checks (api) ==="

for ip in $($K get pods -l app=car-monit-api -o jsonpath='{.items[*].status.podIP}'); do

  printf '%s ' "$ip"

  curl -s -o /dev/null -w '%{http_code}\n' -m 10 -H "X-Internal-Token: $CM_TOKEN" "http://$ip:9902/api/v3/es/readiness" 2>/dev/null || echo fail

done

