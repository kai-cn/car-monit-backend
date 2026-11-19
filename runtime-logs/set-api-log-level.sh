#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Write GitHub Secrets or local configuration from runtime-supplied values only.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 临时切换 api 的 LOG_ROOT_LEVEL（env 第 0 位）以观察启动日志
LEVEL="${1:-info}"
echo "set api LOG_ROOT_LEVEL=$LEVEL"
docker exec k3d-v3-server-0 kubectl patch deployment car-monit-api --type=json \
  -p "[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/env/0/value\",\"value\":\"$LEVEL\"}]"
docker exec k3d-v3-server-0 kubectl rollout restart deployment/car-monit-api
