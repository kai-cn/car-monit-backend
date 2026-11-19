#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== redis-single clients (>1 means backend on 6379) ==="
sudo redis-cli -p 6379 info clients 2>/dev/null | grep connected_clients
echo "=== cluster 7000 state ==="
redis-cli -p 7000 cluster info 2>/dev/null | grep cluster_state || echo "cluster 7000 down"
echo "=== cluster 7000 clients ==="
redis-cli -p 7000 info clients 2>/dev/null | grep connected_clients || true
echo "=== pods ==="
docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' --no-headers 2>&1
echo "=== captcha ==="
bash /mnt/d/work/runtime-logs/captcha-check.sh
