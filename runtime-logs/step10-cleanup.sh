#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
K="docker exec k3d-v3-server-0 kubectl"
echo "=== delete cluster test workloads ==="
$K delete deploy car-monit-api car-monit-backend --ignore-not-found
$K delete svc car-monit-api car-monit-backend --ignore-not-found
$K delete secret car-monit-cluster-secrets --ignore-not-found
sleep 5
echo "=== remaining pods ==="
$K get pods -A 2>&1 | head -12
echo "=== stop cluster-shared redis :6380 ==="
redis-cli -h 127.0.0.1 -p 6380 shutdown nosave >/dev/null 2>&1 || true
sleep 1
redis-cli -h 127.0.0.1 -p 6380 ping 2>&1 || echo "redis 6380 stopped"
echo "=== WSL memory after cleanup ==="
free -h | head -2
