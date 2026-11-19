#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== api pods ==="
docker exec k3d-v3-server-0 kubectl get pods -l app=car-monit-api -o wide 2>&1
echo "=== api logs tail ==="
docker exec k3d-v3-server-0 kubectl logs deployment/car-monit-api --tail=60 2>&1 | tail -45
