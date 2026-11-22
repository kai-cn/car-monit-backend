#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -euo pipefail
W=/home/dev/k3s-build/slim
cp /mnt/d/work/IdeaProjects/car-monit-api-jdk17/pro-business-api/target/pro-business-api-1.0.jar "$W/api.jar"
cp /mnt/d/work/IdeaProjects/car-monit-backend-jdk17/ruoyi-admin/target/ruoyi-admin.jar "$W/backend.jar"
for s in api backend; do docker build -q -t "car-monit-$s:slim" -f "$W/Dockerfile.$s" "$W" | tail -1; done
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -E 'car-monit-(api|backend):slim'
