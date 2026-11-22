#!/usr/bin/env bash

# @description 历史脚本 kafka-roundtrip.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash kafka-roundtrip.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

echo "=== Kafka round-trip via advertised listener 172.18.0.1:9092 ==="

sudo docker exec kafka-wsl bash -c "echo g7test | /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server 172.18.0.1:9092 --topic search-sync 2>&1 | tail -2"

echo "--- consume back ---"

sudo docker exec kafka-wsl timeout 12 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server 172.18.0.1:9092 --topic search-sync --from-beginning --max-messages 1 --timeout-ms 8000 2>&1 | head -3

echo "=== api logs: outbox/relay/producer (proves traffic.sync.enabled=true) ==="

docker exec k3d-v3-server-0 kubectl logs deployment/car-monit-api --tail=800 2>&1 | grep -iE 'outbox|relay|jl_data01|Producer|search_sync|同步' | tail -12

