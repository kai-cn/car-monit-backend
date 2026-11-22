#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
: "${CM_TOKEN:?}"
K="docker exec k3d-v3-server-0 kubectl"
echo "=== nodes ==="
$K get nodes --no-headers
echo "=== pods with creation timestamps ==="
$K get pods -l 'app in (car-monit-api,car-monit-backend)' -o jsonpath='{range .items[*]}{.metadata.name}{" created="}{.metadata.creationTimestamp}{" node="}{.spec.nodeName}{" restarts="}{.status.containerStatuses[0].restartCount}{"\n"}{end}'
echo "=== eviction/scheduling events ==="
$K get events --sort-by=.lastTimestamp 2>/dev/null | grep -Ei 'evict|notready|node|scheduled|killing|terminat' | tail -18
echo "=== per-pod workingSet MiB ==="
for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do
  docker exec "$n" crictl stats -o json 2>/dev/null | jq -r '.stats[]? | select(.attributes.metadata.name | test("backend|api")) | [.attributes.metadata.name, ((.memory.workingSetBytes.value // 0) | tonumber / 1048576 | floor | tostring)] | @tsv' 2>/dev/null | head -8
done
echo "=== endpoints ==="
$K get endpoints car-monit-api car-monit-backend 2>/dev/null | tail -3
echo "=== api NodePort 15x ==="
for i in $(seq 1 15); do curl -s -o /dev/null -w '%{http_code} ' -m 15 -H "X-Internal-Token: $CM_TOKEN" http://172.18.0.2:30902/api/v3/es/readiness; done; echo
echo "=== api list endpoints ==="
curl -s -m 20 -H "X-Internal-Token: $CM_TOKEN" 'http://172.18.0.2:30902/base/section/list?pageNum=1&pageSize=3' | head -c 100; echo
echo "=== backend HTTP (document degraded) ==="
curl -s -m 15 http://172.18.0.2:30989/captchaImage | head -c 140; echo
