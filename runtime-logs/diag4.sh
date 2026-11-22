#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== backend log tail ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=40 2>&1 | tail -40
echo "=== markers ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=300 2>&1 | grep -E 'Started |Application run failed|OutOfMemoryError|StackOverflow|Tomcat started|Exception' | tail -12
echo "=== endpoints raw ==="
for p in 30989 30902; do
  echo "--- port $p ---"
  curl -sv -m 8 "http://172.18.0.2:$p/" 2>&1 | head -12
done
