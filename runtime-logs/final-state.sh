#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
: "${CM_TOKEN:?}"
K="docker exec k3d-v3-server-0 kubectl"
echo "=== deployments / pods ==="
$K get deploy car-monit-api car-monit-backend --no-headers
$K get pods -l 'app in (car-monit-api,car-monit-backend)' --no-headers | awk '{print $1, $2, $3, $4, $7}'
echo "=== endpoints ==="
for i in $(seq 1 6); do curl -s -o /dev/null -w '%{http_code} ' -m 15 -H "X-Internal-Token: $CM_TOKEN" http://172.18.0.2:30902/api/v3/es/readiness; done; echo
curl -s -o /dev/null -w 'backend captcha=%{http_code}\n' -m 15 http://172.18.0.2:30989/captchaImage
echo "=== DB limits ==="
for c in mysql_wsl opengauss; do docker inspect --format '{{.Name}} mem={{.HostConfig.Memory}} oom={{.State.OOMKilled}}' "$c"; done
echo "=== image sizes ==="
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -E 'car-monit-(api|backend|sys)' | sort
echo "=== WSL memory ==="
free -h | head -2
