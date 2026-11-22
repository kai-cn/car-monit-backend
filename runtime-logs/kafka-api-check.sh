#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== api logs kafka/consumer ==="
docker exec k3d-v3-server-0 kubectl logs deployment/car-monit-api --tail=500 2>&1 | grep -iE 'kafka|consumer|subscri|bootstrap|9092|search-sync|OutboxRelay|同步' | tail -25
echo "=== consumer groups list ==="
sudo docker exec kafka-wsl /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list 2>&1
echo "=== describe search-sync-api ==="
sudo docker exec kafka-wsl /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group search-sync-api 2>&1 | head
