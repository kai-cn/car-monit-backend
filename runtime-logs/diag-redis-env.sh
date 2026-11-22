#!/usr/bin/env bash
# @description 历史脚本 diag-redis-env.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash diag-redis-env.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "===== backend redis env ====="
docker exec k3d-v3-server-0 kubectl get deploy car-monit-backend -o yaml | grep -iE 'REDIS'
echo "===== api redis env ====="
docker exec k3d-v3-server-0 kubectl get deploy car-monit-api -o yaml | grep -iE 'REDIS'
echo "===== backend logs (redis/connection) ====="
docker exec k3d-v3-server-0 kubectl logs deployment/car-monit-backend --tail=20 2>&1 | grep -iE 'redis|refused|exception|Connection' | head -10
