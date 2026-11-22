#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a generated configuration to local or remote branches.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 用修正后的 manifests-final.yaml 重置两个 Deployment 到 单节点(6379) 状态
cat /mnt/d/work/runtime-logs/manifests-final.yaml | docker exec -i k3d-v3-server-0 kubectl apply -f -
echo "=== backend redis env ==="
docker exec k3d-v3-server-0 kubectl get deploy car-monit-backend -o yaml | grep -E 'SPRING_DATA_REDIS|REDISCLUSTER'
echo "=== api redis env ==="
docker exec k3d-v3-server-0 kubectl get deploy car-monit-api -o yaml | grep -E 'SPRING_DATA_REDIS|REDISCLUSTER'
echo "=== rollout restart ==="
docker exec k3d-v3-server-0 kubectl rollout restart deployment/car-monit-backend deployment/car-monit-api
