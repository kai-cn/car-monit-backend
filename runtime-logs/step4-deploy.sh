#!/usr/bin/env bash
# @description 历史脚本 step4-deploy.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash step4-deploy.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
: "${CM_MYSQL_PWD:?} ${CM_OGAUSS_PWD:?} ${CM_TOKEN:?} ${CM_EXPORT_SECRET:?}"
K="docker exec -i k3d-v3-server-0 kubectl"

echo "=== recreate secret ==="
docker exec k3d-v3-server-0 kubectl delete secret car-monit-cluster-secrets --ignore-not-found >/dev/null 2>&1 || true
docker exec k3d-v3-server-0 kubectl create secret generic car-monit-cluster-secrets \
  --from-literal="mysql-password=$CM_MYSQL_PWD" \
  --from-literal="opengauss-password=$CM_OGAUSS_PWD" \
  --from-literal="internal-token=$CM_TOKEN" \
  --from-literal="export-secret=$CM_EXPORT_SECRET" >/dev/null

echo "=== delete stale deployments and apply tuned manifest ==="
docker exec k3d-v3-server-0 kubectl delete deploy car-monit-api car-monit-backend --ignore-not-found >/dev/null 2>&1 || true
sleep 3
docker exec -i k3d-v3-server-0 kubectl apply -f - < /mnt/d/work/runtime-logs/manifests-final.yaml

echo "=== wait for 1/1 each (max 240s) ==="
for i in $(seq 1 24); do
  out=$(docker exec k3d-v3-server-0 kubectl get deploy car-monit-api car-monit-backend --no-headers 2>/dev/null)
  echo "poll $i: $(echo "$out" | tr '\n' ' ')"
  r=$(echo "$out" | awk '{s+=$3} END{print s}')
  w=$(echo "$out" | awk '{s+=$2} END{print s}')
  if [ "${r:-0}" = "2" ] && [ "${w:-0}" = "2" ]; then echo "READY"; break; fi
  sleep 10
done

echo "=== pods ==="
docker exec k3d-v3-server-0 kubectl get pods -o wide 2>&1 | grep -E 'car-monit|NAME'
echo "=== OOM / restart check ==="
docker exec k3d-v3-server-0 kubectl describe pods -l app=car-monit-api 2>&1 | grep -E 'OOMKilled|Restart Count|Limits|Requests' | head -8
docker exec k3d-v3-server-0 kubectl describe pods -l app=car-monit-backend 2>&1 | grep -E 'OOMKilled|Restart Count|Limits|Requests' | head -8
echo "=== crictl stats (if available) ==="
for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do
  docker exec "$n" crictl stats 2>/dev/null | grep -E 'car-monit|CONTAINER' | head -4 || true
done
echo "=== NodePort endpoints from WSL VM ==="
curl -s -o /dev/null -w 'api no-token http=%{http_code}\n' -m 15 http://172.18.0.2:30902/api/v3/es/readiness
curl -s -o /dev/null -w 'api with-token http=%{http_code}\n' -m 15 -H "X-Internal-Token: $CM_TOKEN" http://172.18.0.2:30902/api/v3/es/readiness
curl -s -o /dev/null -w 'api section http=%{http_code}\n' -m 20 -H "X-Internal-Token: $CM_TOKEN" 'http://172.18.0.2:30902/base/section/list?pageNum=1&pageSize=5'
curl -s -o /dev/null -w 'backend captcha http=%{http_code}\n' -m 15 http://172.18.0.2:30989/captchaImage
