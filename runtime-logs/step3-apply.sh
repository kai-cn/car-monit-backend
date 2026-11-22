#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -euo pipefail
: "${CM_MYSQL_PWD:?} ${CM_OGAUSS_PWD:?} ${CM_TOKEN:?} ${CM_EXPORT_SECRET:?}"
K="docker exec -i k3d-v3-server-0 kubectl"

echo "=== create secret (values come from process environment only) ==="
docker exec k3d-v3-server-0 kubectl delete secret car-monit-cluster-secrets --ignore-not-found >/dev/null 2>&1 || true
docker exec k3d-v3-server-0 kubectl create secret generic car-monit-cluster-secrets \
  --from-literal="mysql-password=$CM_MYSQL_PWD" \
  --from-literal="opengauss-password=$CM_OGAUSS_PWD" \
  --from-literal="internal-token=$CM_TOKEN" \
  --from-literal="export-secret=$CM_EXPORT_SECRET" >/dev/null

echo "=== apply manifest (1 replica each first) ==="
docker exec -i k3d-v3-server-0 kubectl apply -f - < /mnt/d/work/runtime-logs/manifests.yaml

echo "=== wait for first pods (max 240s) ==="
for i in $(seq 1 24); do
  out=$(docker exec k3d-v3-server-0 kubectl get deploy car-monit-api car-monit-backend --no-headers 2>/dev/null)
  echo "poll $i: $(echo "$out" | tr '\n' ' ')"
  if echo "$out" | awk '{print $3}' | grep -qv '^1$'; then :; fi
  ready=$(echo "$out" | awk '{s+=$3} END{print s}')
  want=$(echo "$out" | awk '{s+=$2} END{print s}')
  if [ "${ready:-0}" = "${want:-0}" ] && [ "${want:-0}" = "2" ]; then echo "BOTH READY"; break; fi
  sleep 10
done
echo "=== pods ==="
docker exec k3d-v3-server-0 kubectl get pods -o wide 2>&1 | grep -E 'car-monit|NAME'
echo "=== container memory (docker stats snapshot) ==="
docker stats --no-stream --format '{{.Name}} {{.MemUsage}} {{.MemPerc}}' 2>/dev/null | grep -E 'k3d-v3' | head -6
echo "=== startup log tails ==="
for d in car-monit-api car-monit-backend; do
  p=$(docker exec k3d-v3-server-0 kubectl get pods -l app="$d" -o name 2>/dev/null | head -1)
  echo "--- $p ---"
  docker exec k3d-v3-server-0 kubectl logs "$p" --tail=12 2>&1 | tail -12
done
