#!/usr/bin/env bash

# @description 历史脚本 step8-fault.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash step8-fault.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

K="docker exec k3d-v3-server-0 kubectl"

TS() { date '+%H:%M:%S'; }



echo "############ A: delete one pod ############"

VICTIM=$($K get pods -l app=car-monit-api -o name | head -1)

echo "$(TS) deleting $VICTIM"

$K delete "$VICTIM" >/dev/null

for i in $(seq 1 18); do

  sleep 10

  d=$($K get deploy car-monit-api --no-headers 2>/dev/null)

  echo "$(TS) poll $i api=$d"

  r=$(echo "$d" | awk '{print $3}')

  [ "$r" = "3/3" ] && { echo "$(TS) A-RECOVERED"; break; }

done

echo "=== api pods after A ==="

$K get pods -l app=car-monit-api -o wide



echo "############ B: stop node k3d-v3-agent-0 ############"

echo "$(TS) docker stop k3d-v3-agent-0"

docker stop k3d-v3-agent-0 >/dev/null

for i in $(seq 1 48); do

  sleep 10

  nodes=$($K get nodes --no-headers 2>/dev/null | awk '{print $1":"$2}' | tr '\n' ' ')

  da=$($K get deploy car-monit-api --no-headers 2>/dev/null | awk '{print $3}')

  db=$($K get deploy car-monit-backend --no-headers 2>/dev/null | awk '{print $3}')

  pend=$($K get pods -l 'app in (car-monit-api,car-monit-backend)' --no-headers 2>/dev/null | grep -c Pending || true)

  echo "$(TS) poll $i api=$da backend=$db pending=${pend:-0} nodes=[$nodes]"

  if [ "$da" = "3/3" ] && [ "$db" = "3/3" ] && [ "$i" -ge 6 ]; then echo "$(TS) B-RECOVERED-WHILE-NODE-DOWN"; break; fi

done

echo "=== pods while node down ==="

$K get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide

echo "=== events (eviction / scheduling) ==="

$K get events --sort-by=.lastTimestamp 2>/dev/null | grep -Ei 'evict|notready|scheduled|node' | tail -12



echo "############ C: restart node ############"

echo "$(TS) docker start k3d-v3-agent-0"

docker start k3d-v3-agent-0 >/dev/null

for i in $(seq 1 24); do

  sleep 10

  nodes=$($K get nodes --no-headers 2>/dev/null | awk '{print $1":"$2}' | tr '\n' ' ')

  da=$($K get deploy car-monit-api --no-headers 2>/dev/null | awk '{print $3}')

  db=$($K get deploy car-monit-backend --no-headers 2>/dev/null | awk '{print $3}')

  total=$($K get pods -l 'app in (car-monit-api,car-monit-backend)' --no-headers 2>/dev/null | wc -l)

  echo "$(TS) poll $i api=$da backend=$db total_pods=$total nodes=[$nodes]"

  if echo "$nodes" | grep -q 'k3d-v3-agent-0:Ready' && [ "$da" = "3/3" ] && [ "$db" = "3/3" ] && [ "$total" = "6" ]; then echo "$(TS) C-STABLE"; break; fi

done

echo "=== final ==="

$K get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide

