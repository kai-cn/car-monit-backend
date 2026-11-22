#!/usr/bin/env bash

# @description 历史脚本 final-verify.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash final-verify.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

echo "=== pods ==="

docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide 2>&1 | grep -E 'NAME|api-|backend-'

echo "=== api pod env REDIS (expect HOST/PORT only, no CLUSTER_NODES) ==="

docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-api -- bash -c 'env | grep -i redis' 2>&1

echo "=== captcha body (expect img) ==="

curl -s -m 10 http://172.18.0.5:30989/captchaImage | head -c 60

echo

echo "=== kafka consumer groups ==="

sudo docker exec kafka-wsl /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list 2>&1

echo "=== ES health ==="

curl -s -m 5 http://172.18.0.1:9200/_cluster/health 2>&1

echo

echo "=== redis single version ==="

redis-cli -p 6379 info server 2>/dev/null | grep redis_version

