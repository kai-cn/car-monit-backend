#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== pod RESP PING to 172.18.0.1:6379 (expect +PONG) ==="
docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-backend -- bash -c 'exec 3<>/dev/tcp/172.18.0.1/6379; printf "*1\r\n\$4\r\nPING\r\n" >&3; timeout 5 head -c 24 <&3; echo " <END>"' 2>&1
echo "=== pod env REDIS ==="
docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-backend -- bash -c 'env | grep -i redis' 2>&1
