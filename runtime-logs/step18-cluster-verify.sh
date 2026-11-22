#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
: "${CM_TOKEN:?}"
K="docker exec k3d-v3-server-0 kubectl"
echo "=== wait real 1/1 + HTTP ==="
for i in $(seq 1 24); do
  sleep 10
  d=$($K get deploy car-monit-api car-monit-backend --no-headers 2>/dev/null)
  a=$(curl -s -o /dev/null -w '%{http_code}' -m 8 -H "X-Internal-Token: $CM_TOKEN" http://172.18.0.2:30902/api/v3/es/readiness 2>/dev/null || true)
  b=$(curl -s -o /dev/null -w '%{http_code}' -m 8 http://172.18.0.2:30989/captchaImage 2>/dev/null || true)
  echo "poll $i: $(echo "$d" | tr '\n' ' ') api=$a backend=$b"
  ra=$(echo "$d" | awk '{s+=$2} END{print s}')
  if [ "${ra:-0}" = "2" ] && [ "$a" = "200" ] && [ "$b" = "200" ]; then echo "VERIFY OK"; break; fi
done
echo "=== endpoints ==="
curl -s -o /dev/null -w 'api no-token=%{http_code}\n' -m 15 http://172.18.0.2:30902/api/v3/es/readiness
curl -s -m 20 -H "X-Internal-Token: $CM_TOKEN" 'http://172.18.0.2:30902/base/section/list?pageNum=1&pageSize=3' | head -c 90; echo
CAP=$(curl -s -m 20 http://172.18.0.2:30989/captchaImage)
echo "captcha has_img=$(echo "$CAP" | jq -r '.img != null' 2>/dev/null) uuid=$(echo "$CAP" | jq -r .uuid 2>/dev/null)"
echo "=== scale to 3+3 if memory allows ==="
free -h | head -2
$K scale deploy/car-monit-api --replicas=3
$K scale deploy/car-monit-backend --replicas=3
for i in $(seq 1 24); do
  sleep 10
  d=$($K get deploy car-monit-api car-monit-backend --no-headers 2>/dev/null)
  echo "scale poll $i: $(echo "$d" | tr '\n' ' ')"
  ra=$(echo "$d" | awk '{s+=$2} END{print s}')
  [ "${ra:-0}" = "6" ] && { echo "3+3 READY"; break; }
done
echo "=== final pods / restarts ==="
$K get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide
echo "=== endpoints after scale ==="
for i in $(seq 1 8); do curl -s -o /dev/null -w '%{http_code} ' -m 15 -H "X-Internal-Token: $CM_TOKEN" http://172.18.0.2:30902/api/v3/es/readiness; done; echo
echo "=== pod memory (MiB) ==="
for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do
  docker exec "$n" crictl stats -o json 2>/dev/null | jq -r '.stats[]? | select(.attributes.metadata.name | test("backend|api")) | [.attributes.metadata.name, ((.memory.workingSetBytes.value // 0) | tonumber / 1048576 | floor | tostring)] | @tsv' 2>/dev/null | head -8
done
echo "=== DB limits ==="
for c in mysql_wsl opengauss; do docker inspect --format '{{.Name}} mem={{.HostConfig.Memory}} oom={{.State.OOMKilled}}' "$c"; done
