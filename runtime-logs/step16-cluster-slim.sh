#!/usr/bin/env bash

# @description 历史脚本 step16-cluster-slim.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash step16-cluster-slim.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

: "${CM_MYSQL_PWD:?} ${CM_OGAUSS_PWD:?} ${CM_TOKEN:?} ${CM_EXPORT_SECRET:?}"

K="docker exec k3d-v3-server-0 kubectl"

echo "=== import slim images into k3d ==="

k3d image import car-monit-api:slim car-monit-backend:slim -c v3 2>&1 | tail -2

echo "=== free memory from docker smoke containers ==="

docker rm -f slim-api slim-be >/dev/null 2>&1 || true

echo "=== recreate secret + apply slim manifest ==="

$K delete secret car-monit-cluster-secrets --ignore-not-found >/dev/null 2>&1 || true

$K create secret generic car-monit-cluster-secrets \

  --from-literal="mysql-password=$CM_MYSQL_PWD" \

  --from-literal="opengauss-password=$CM_OGAUSS_PWD" \

  --from-literal="internal-token=$CM_TOKEN" \

  --from-literal="export-secret=$CM_EXPORT_SECRET" >/dev/null

$K delete deploy car-monit-api car-monit-backend --ignore-not-found >/dev/null 2>&1 || true

sleep 3

$K apply -f - < /mnt/d/work/runtime-logs/manifests-final.yaml

echo "=== wait 1/1 (max 240s) ==="

for i in $(seq 1 24); do

  sleep 10

  d=$($K get deploy car-monit-api car-monit-backend --no-headers 2>/dev/null)

  echo "poll $i: $(echo "$d" | tr '\n' ' ')"

  r=$(echo "$d" | awk '{s+=$3} END{print s}')

  [ "${r:-0}" = "2" ] && { echo "1+1 READY"; break; }

done

echo "=== endpoints at 400Mi ==="

curl -s -o /dev/null -w 'api no-token=%{http_code}\n' -m 15 http://172.18.0.2:30902/api/v3/es/readiness

curl -s -o /dev/null -w 'api with-token=%{http_code}\n' -m 15 -H "X-Internal-Token: $CM_TOKEN" http://172.18.0.2:30902/api/v3/es/readiness

curl -s -o /dev/null -w 'backend captcha=%{http_code}\n' -m 15 http://172.18.0.2:30989/captchaImage

curl -s -m 20 -H "X-Internal-Token: $CM_TOKEN" 'http://172.18.0.2:30902/base/section/list?pageNum=1&pageSize=3' | head -c 90; echo

echo "=== WSL free memory before scaling ==="

free -h | head -2

echo "=== scale to 3+3 ==="

$K scale deploy/car-monit-api --replicas=3

$K scale deploy/car-monit-backend --replicas=3

for i in $(seq 1 24); do

  sleep 10

  d=$($K get deploy car-monit-api car-monit-backend --no-headers 2>/dev/null)

  echo "scale poll $i: $(echo "$d" | tr '\n' ' ')"

  r=$(echo "$d" | awk '{s+=$3} END{print s}')

  [ "${r:-0}" = "6" ] && { echo "3+3 READY"; break; }

done

echo "=== final pods / memory ==="

$K get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide

for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do

  docker exec "$n" crictl stats -o json 2>/dev/null | jq -r '.stats[]? | select(.attributes.metadata.name | test("backend|api")) | [.attributes.metadata.name, ((.memory.workingSetBytes.value // 0) | tonumber / 1048576 | floor | tostring)] | @tsv' 2>/dev/null | head -8

done

echo "=== DB limits still in force ==="

for c in mysql_wsl opengauss; do docker inspect --format '{{.Name}} mem={{.HostConfig.Memory}} oom={{.State.OOMKilled}}' "$c"; done

