#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== pods ==="
docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide 2>&1 | grep -E 'NAME|api-|backend-'
echo "=== api logs (ES/Kafka/engine) ==="
docker exec k3d-v3-server-0 kubectl logs deployment/car-monit-api --tail=100 2>&1 | grep -iE 'ES配置|elasticsearch|kafka|search-sync|V3引擎|同步引擎|engine' | tail -15
echo "=== captcha ==="
bash /mnt/d/work/runtime-logs/captcha-check.sh
echo "=== ES indices ==="
curl -s -m 5 http://172.18.0.1:9200/_cat/indices?v 2>&1 | head
echo "=== Kafka search-sync topic ==="
sudo docker exec kafka-wsl /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic search-sync 2>&1 | head -3
