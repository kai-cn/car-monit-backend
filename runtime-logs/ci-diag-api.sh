#!/usr/bin/env bash

# @description 历史脚本 ci-diag-api.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash ci-diag-api.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

echo "=== api pods ==="

docker exec k3d-v3-server-0 kubectl get pods -l app=car-monit-api -o wide 2>&1

echo "=== api logs tail ==="

docker exec k3d-v3-server-0 kubectl logs deployment/car-monit-api --tail=60 2>&1 | tail -45

