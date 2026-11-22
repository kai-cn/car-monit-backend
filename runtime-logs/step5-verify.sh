#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
: "${CM_TOKEN:?}"
echo "=== wait 180s and watch restarts / captcha ==="
for i in $(seq 1 18); do
  sleep 10
  pods=$(docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' --no-headers 2>/dev/null)
  restarts=$(echo "$pods" | awk '{s+=$4} END{print s}')
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 8 http://172.18.0.2:30989/captchaImage 2>/dev/null || true)
  acode=$(curl -s -o /dev/null -w '%{http_code}' -m 8 -H "X-Internal-Token: $CM_TOKEN" http://172.18.0.2:30902/api/v3/es/readiness 2>/dev/null || true)
  echo "poll $i restarts=${restarts:-0} backend_captcha=$code api_readiness=$acode"
  if [ "$code" = "200" ] && [ "$acode" = "200" ] && [ "$i" -ge 12 ]; then echo "STABLE"; break; fi
done
echo "=== final pods ==="
docker exec k3d-v3-server-0 kubectl get pods -o wide | grep car-monit
echo "=== final describe ==="
docker exec k3d-v3-server-0 kubectl describe pod -l app=car-monit-backend 2>&1 | grep -E 'Last State|Reason|Exit Code|Restart Count|OOMKilled' | head -8
