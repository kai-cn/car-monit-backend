#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== backend non-ERROR log samples ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=200 2>/dev/null | grep -E 'INFO|DEBUG|TRACE|Consume Time|Execute SQL' | head -12
echo "=== backend log level distribution ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=200 2>/dev/null | grep -oE ' (INFO|DEBUG|TRACE|WARN|ERROR) ' | sort | uniq -c
echo "=== first 12 lines ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=200 2>/dev/null | head -12
