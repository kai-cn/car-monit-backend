#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
BE=http://172.18.0.2:30989
echo "=== wait until backend HTTP responds (max 240s) ==="
for i in $(seq 1 24); do
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 8 "$BE/captchaImage" 2>/dev/null || true)
  echo "poll $i captcha=$code"
  [ "$code" = "200" ] && break
  sleep 10
done
echo "=== login WITHOUT captcha code (code validation is skipped when blank) ==="
LOGIN=$(curl -s -m 25 -X POST -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Admin@2025-","code":"","uuid":""}' "$BE/login")
echo "login=$(echo "$LOGIN" | head -c 200)"
TOK=$(echo "$LOGIN" | jq -r .token 2>/dev/null || true)
echo "token_len=${#TOK}"
if [ -n "$TOK" ] && [ "$TOK" != "null" ]; then
  echo "=== authenticated endpoints ==="
  for u in /getInfo /getRouters '/system/user/list?pageNum=1&pageSize=5' '/manager/carinfo/list?pageNum=1&pageSize=5' /monitor/server; do
    printf '%-50s ' "$u"
    curl -s -o /dev/null -w 'http=%{http_code}\n' -m 25 -H "Authorization: Bearer $TOK" "$BE$u"
  done
  echo "=== cross-service export submit ==="
  curl -s -m 30 -X POST -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
    -d '{"type":"snapshot","startTime":"2025-11-01 00:00:00","endTime":"2025-11-30 23:59:59"}' \
    "$BE/manager/bigScreen/export/display" | head -c 220; echo
fi
echo "=== restarts ==="
docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' --no-headers
