#!/usr/bin/env bash
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
