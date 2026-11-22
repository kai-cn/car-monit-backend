#!/usr/bin/env bash

# @description 历史脚本 step21-final-verify.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash step21-final-verify.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

: "${CM_TOKEN:?}"

K="docker exec k3d-v3-server-0 kubectl"

echo "=== apply updated manifest (32m class space) ==="

$K apply -f - < /mnt/d/work/runtime-logs/manifests-final.yaml 2>&1 | head -6

echo "=== rollout status ==="

$K rollout status deploy/car-monit-api --timeout=360s 2>&1 | tail -2

$K rollout status deploy/car-monit-backend --timeout=360s 2>&1 | tail -2

echo "=== pods ==="

$K get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide

echo "=== new pod log level check (per app, newest pod) ==="

for app in car-monit-api car-monit-backend; do

  p=$($K get pods -l app="$app" --sort-by=.metadata.creationTimestamp --no-headers 2>/dev/null | tail -1 | awk '{print $1}')

  logs=$($K logs "$p" --tail=200 2>/dev/null)

  total=$(echo "$logs" | wc -l)

  errs=$(echo "$logs" | grep -c 'ERROR' || true)

  noise=$(echo "$logs" | grep -cE '\|-INFO| INFO | DEBUG | TRACE |Consume Time|Execute SQL' || true)

  echo "$app pod=$p lines=$total error_lines=$errs non_error_lines=$noise"

  echo "$logs" | head -4

done

echo "=== endpoints ==="

curl -s -o /dev/null -w 'api no-token=%{http_code}\n' -m 15 http://172.18.0.2:30902/api/v3/es/readiness

curl -s -o /dev/null -w 'api readiness=%{http_code}\n' -m 15 -H "X-Internal-Token: $CM_TOKEN" http://172.18.0.2:30902/api/v3/es/readiness

curl -s -o /dev/null -w 'backend captcha=%{http_code}\n' -m 15 http://172.18.0.2:30989/captchaImage

echo "=== pod memory MiB ==="

for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do

  docker exec "$n" crictl stats -o json 2>/dev/null | jq -r '.stats[]? | select(.attributes.metadata.name | test("backend|api")) | [.attributes.metadata.name, ((.memory.workingSetBytes.value // 0) | tonumber / 1048576 | floor | tostring)] | @tsv' 2>/dev/null | head -8

done

echo "=== DB limits ==="

for c in mysql_wsl opengauss; do docker inspect --format '{{.Name}} mem={{.HostConfig.Memory}} oom={{.State.OOMKilled}}' "$c"; done

