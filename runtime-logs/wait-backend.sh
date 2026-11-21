#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
for i in $(seq 1 20); do
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://172.18.0.2:30989/captchaImage 2>/dev/null || true)
  st=$(docker exec k3d-v3-server-0 kubectl get deploy car-monit-backend --no-headers 2>/dev/null | awk '{print $3}')
  echo "poll $i deploy_ready=$st captcha=$code"
  [ "$code" = "200" ] && break
  sleep 10
done
echo "=== backend markers ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=200 2>&1 | grep -E 'Started |Application run failed|OutOfMemoryError|CodeCache is full|Tomcat started' | head -10
echo "=== pod describe last state ==="
docker exec k3d-v3-server-0 kubectl describe pod -l app=car-monit-backend 2>&1 | grep -E 'Last State|Reason|Exit Code|Restart Count|OOMKilled' | head -8
