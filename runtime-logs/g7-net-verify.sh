#!/usr/bin/env bash
# @description 历史脚本 g7-net-verify.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash g7-net-verify.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== ES reachable from k3d node (172.18.0.1:9200) ==="
docker exec k3d-v3-server-0 wget -qO- -T 5 http://172.18.0.1:9200 2>&1 | head -c 200
echo
echo "=== Kafka consumer groups (expect search-sync-api) ==="
sudo docker exec kafka-wsl /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list 2>&1
echo "=== Kafka topics ==="
sudo docker exec kafka-wsl /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list 2>&1
