#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== pod status ==="
docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide 2>&1
echo "=== last termination reason ==="
docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' -o jsonpath='{range .items[*]}{.metadata.name}{" last="}{.status.containerStatuses[0].lastState.terminated.reason}{" exit="}{.status.containerStatuses[0].lastState.terminated.exitCode}{"\n"}{end}' 2>&1
echo "=== events (OOM/unhealthy) ==="
docker exec k3d-v3-server-0 kubectl get events --sort-by=.lastTimestamp 2>&1 | grep -iE 'OOM|Killing|Unhealthy|Failed|BackOff' | tail -12
echo "=== WSL mem ==="
free -m | head -2
