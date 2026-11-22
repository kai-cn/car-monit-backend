#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a generated configuration to local or remote branches.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== kubectl apply dry-run ==="
docker exec -i k3d-v3-server-0 kubectl apply --dry-run=client -f - < /mnt/d/work/runtime-logs/manifests-final.yaml 2>&1 | head -20
echo "=== file head ==="
head -8 /mnt/d/work/runtime-logs/manifests-final.yaml
echo "=== deployments ==="
docker exec k3d-v3-server-0 kubectl get deploy 2>&1 | head -12
