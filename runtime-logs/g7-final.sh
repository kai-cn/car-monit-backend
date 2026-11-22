#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== pods ==="
docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide 2>&1 | grep -E 'NAME|api-|backend-'
echo "=== captcha ==="
bash /mnt/d/work/runtime-logs/captcha-check.sh
echo "=== kafka consumer groups ==="
sudo docker exec kafka-wsl /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list 2>&1
echo "=== ES health ==="
curl -s -m 5 http://172.18.0.1:9200/_cluster/health 2>&1
