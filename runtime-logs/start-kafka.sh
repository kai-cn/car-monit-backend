#!/usr/bin/env bash

# @description 历史脚本 start-kafka.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash start-kafka.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 在 WSL 启动 Kafka 4.0.0（KRaft 单节点，400M 内存限制），广播 172.18.0.1:9092

set -e

CID=$(openssl rand -base64 16 | tr -d '=' | head -c 22)

echo "cluster_id=$CID"

docker run -d --name kafka-wsl --memory=400m --restart=unless-stopped \

  -p 172.18.0.1:9092:9092 \

  -e KAFKA_NODE_ID=1 \

  -e KAFKA_PROCESS_ROLES=broker,controller \

  -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@127.0.0.1:9093 \

  -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093 \

  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://172.18.0.1:9092 \

  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \

  -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \

  -e KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT \

  -e KAFKA_AUTO_CREATE_TOPICS_ENABLE=true \

  -e KAFKA_AUTO_FORMAT=true \

  -e CLUSTER_ID=$CID \

  -e KAFKA_HEAP_OPTS="-Xmx256m -Xms256m" \

  -e KAFKA_JMX_OPTS= \

  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \

  -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 \

  -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 \

  apache/kafka:4.0.0

echo "=== waiting for Kafka ==="

for i in $(seq 1 40); do

  if docker exec kafka-wsl /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 >/dev/null 2>&1; then echo "Kafka UP after ${i}x3s"; break; fi

  sleep 3

done

echo "=== topic list ==="

docker exec kafka-wsl /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list 2>&1 | head

