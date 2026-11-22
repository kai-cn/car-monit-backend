#!/usr/bin/env bash

# @description 历史脚本 kafka-api-check.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash kafka-api-check.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

echo "=== api logs kafka/consumer ==="

docker exec k3d-v3-server-0 kubectl logs deployment/car-monit-api --tail=500 2>&1 | grep -iE 'kafka|consumer|subscri|bootstrap|9092|search-sync|OutboxRelay|同步' | tail -25

echo "=== consumer groups list ==="

sudo docker exec kafka-wsl /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list 2>&1

echo "=== describe search-sync-api ==="

sudo docker exec kafka-wsl /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group search-sync-api 2>&1 | head

