#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "===== backend redis env ====="
docker exec k3d-v3-server-0 kubectl get deploy car-monit-backend -o yaml | grep -iE 'REDIS'
echo "===== api redis env ====="
docker exec k3d-v3-server-0 kubectl get deploy car-monit-api -o yaml | grep -iE 'REDIS'
echo "===== backend logs (redis/connection) ====="
docker exec k3d-v3-server-0 kubectl logs deployment/car-monit-backend --tail=20 2>&1 | grep -iE 'redis|refused|exception|Connection' | head -10
