#!/usr/bin/env bash

# @description 历史脚本 mem-inspect.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash mem-inspect.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

echo "=== pods ==="

docker exec k3d-v3-server-0 kubectl get pods -o wide | grep car-monit

echo "=== describe backend (memory / last state) ==="

docker exec k3d-v3-server-0 kubectl describe pod -l app=car-monit-backend 2>&1 | grep -E 'Limits|Requests|Last State|Reason|Exit Code|Restart Count|OOMKilled|memory' | head -14

echo "=== crictl stats json (per node) ==="

for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do

  echo "--- $n ---"

  docker exec "$n" crictl stats -o json 2>/dev/null | jq -r '.stats[]? | select(.attributes.metadata.name | test("backend|api")) | [.attributes.metadata.name, (.memory.workingSetBytes.value|tostring), (.memory.usageBytes.value|tostring)] | @tsv' 2>/dev/null | head -8 || true

done

echo "=== backend log errors ==="

docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=120 2>&1 | grep -E 'Started |OutOfMemoryError|Application run failed' | tail -8

