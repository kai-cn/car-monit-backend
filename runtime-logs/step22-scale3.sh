#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
: "${CM_TOKEN:?}"
K="docker exec k3d-v3-server-0 kubectl"
$K scale deploy/car-monit-api --replicas=3
$K scale deploy/car-monit-backend --replicas=3
$K rollout status deploy/car-monit-api --timeout=300s 2>&1 | tail -1
$K rollout status deploy/car-monit-backend --timeout=300s 2>&1 | tail -1
echo "=== final ==="
$K get deploy car-monit-api car-monit-backend --no-headers
$K get pods -l 'app in (car-monit-api,car-monit-backend)' --no-headers | awk '{print $1, $2, $3, $4, $7}'
echo "=== endpoints ==="
for i in 1 2 3 4 5 6; do curl -s -o /dev/null -w '%{http_code} ' -m 15 -H "X-Internal-Token: $CM_TOKEN" http://172.18.0.2:30902/api/v3/es/readiness; done; echo
curl -s -o /dev/null -w 'backend captcha=%{http_code}\n' -m 15 http://172.18.0.2:30989/captchaImage
echo "=== log noise (newest pod per app) ==="
for app in car-monit-api car-monit-backend; do
  p=$($K get pods -l app="$app" --sort-by=.metadata.creationTimestamp --no-headers | tail -1 | awk '{print $1}')
  logs=$($K logs "$p" --tail=100 2>/dev/null)
  echo "$app $p lines=$(echo "$logs" | wc -l) non_error_business=$(echo "$logs" | grep -cE ' INFO | DEBUG | TRACE |Consume Time|Execute SQL' || true)"
done
