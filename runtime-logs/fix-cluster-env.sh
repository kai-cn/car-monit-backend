#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== delete deployments for a clean env rebuild ==="
docker exec k3d-v3-server-0 kubectl delete deployment car-monit-backend car-monit-api 2>&1
echo "=== re-apply clean manifest (no CLUSTER_NODES) ==="
cat /mnt/d/work/runtime-logs/manifests-final.yaml | docker exec -i k3d-v3-server-0 kubectl apply -f - 2>&1 | grep -E 'created|configured|unchanged'
echo "=== new backend pod env REDIS ==="
sleep 15
docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-backend -- bash -c 'env | grep -i redis' 2>&1
