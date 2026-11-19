#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== raw /proc/net/tcp in backend pod (local/rem ports in hex) ==="
docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-backend -- sh -c 'cat /proc/net/tcp' 2>&1 | head -30
