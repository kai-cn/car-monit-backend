#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== pods ==="
docker exec k3d-v3-server-0 kubectl get pods -o wide | grep car-monit
echo "=== describe backend (memory / last state) ==="
docker exec k3d-v3-server-0 kubectl describe pod -l app=car-monit-backend 2>&1 | grep -E 'Limits|Requests|Last State|Reason|Exit Code|Restart Count|OOMKilled|memory' | head -14
echo "=== crictl stats json (per node) ==="
for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do
  echo "--- $n ---"
  docker exec "$n" crictl stats -o json 2>/dev/null | jq -r '.stats[]? | select(.attributes.metadata.name | test("backend|api")) | [.attributes.metadata.name, (.memory.workingSetBytes.value|tostring), (.memory.usageBytes.value|tostring)] | @tsv' 2>/dev/null | head -8 || true
done
echo "=== backend log errors ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=120 2>&1 | grep -E 'Started |OutOfMemoryError|Application run failed' | tail -8
