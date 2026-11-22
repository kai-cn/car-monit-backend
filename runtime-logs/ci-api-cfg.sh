#!/usr/bin/env bash
# @description 历史脚本 ci-api-cfg.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash ci-api-cfg.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
docker exec k3d-v3-server-0 kubectl get deploy car-monit-api -o yaml 2>/dev/null \
  | grep -E 'master.url|driverClassName|p6spy|SPRING_DATASOURCE|TRAFFIC_API_INTERNAL_TOKEN|TRAFFIC_INTERNAL_TOKEN|EXPORT_|ELASTICSEARCH_HOST|SPRING_KAFKA_BOOTSTRAP_SERVERS|SPRING_DATA_REDIS' | head -30
