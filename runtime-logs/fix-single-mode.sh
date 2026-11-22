#!/usr/bin/env bash

# @description 历史脚本 fix-single-mode.sh：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash fix-single-mode.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 强制把两个 Deployment 的 Redis 配置重置为 单节点(6379)，移除所有 cluster 相关键

KCTL="docker exec k3d-v3-server-0 kubectl"

for d in car-monit-backend car-monit-api; do

  $KCTL set env deployment/$d SPRING_DATA_REDIS_HOST=172.18.0.1 SPRING_DATA_REDIS_PORT=6379

  $KCTL set env deployment/$d --remove=SPRING_DATA_REDIS_CLUSTER_NODES 2>/dev/null

  $KCTL set env deployment/$d --remove=REDISCLUSTER_CLUSTERNODES 2>/dev/null

done

echo "===== backend redis env (should be HOST/PORT only) ====="

$KCTL get deploy car-monit-backend -o yaml | grep -E 'SPRING_DATA_REDIS|REDISCLUSTER'

echo "===== api redis env (should be HOST/PORT only) ====="

$KCTL get deploy car-monit-api -o yaml | grep -E 'SPRING_DATA_REDIS|REDISCLUSTER'

echo "===== rollout restart ====="

$KCTL rollout restart deployment/car-monit-backend deployment/car-monit-api

