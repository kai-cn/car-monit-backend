#!/usr/bin/env bash

# @description 历史脚本 set-api-log-level.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash set-api-log-level.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Write GitHub Secrets or local configuration from runtime-supplied values only.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 临时切换 api 的 LOG_ROOT_LEVEL（env 第 0 位）以观察启动日志

LEVEL="${1:-info}"

echo "set api LOG_ROOT_LEVEL=$LEVEL"

docker exec k3d-v3-server-0 kubectl patch deployment car-monit-api --type=json \

  -p "[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/env/0/value\",\"value\":\"$LEVEL\"}]"

docker exec k3d-v3-server-0 kubectl rollout restart deployment/car-monit-api

