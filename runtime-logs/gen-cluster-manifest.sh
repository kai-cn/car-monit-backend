#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 由 manifests-final.yaml(单节点) 生成 manifests-cluster.yaml(集群)：
#  - 把 SPRING_DATA_REDIS_HOST 行替换为 CLUSTER_NODES + REDISCLUSTER_CLUSTERNODES
#  - 删除 SPRING_DATA_REDIS_PORT 行（集群模式不能同时留 host/port）
NODES="172.18.0.1:7000,172.18.0.1:7001,172.18.0.1:7002,172.18.0.1:7003,172.18.0.1:7004,172.18.0.1:7005"
awk -v nodes="$NODES" '
  /SPRING_DATA_REDIS_HOST, value: 172.18.0.1/ {
    print "            - { name: SPRING_DATA_REDIS_CLUSTER_NODES, value: \"" nodes "\" }";
    print "            - { name: REDISCLUSTER_CLUSTERNODES, value: \"" nodes "\" }";
    next;
  }
  /SPRING_DATA_REDIS_PORT, value: "6379"/ { next }
  { print }
' /mnt/d/work/runtime-logs/manifests-final.yaml > /mnt/d/work/runtime-logs/manifests-cluster.yaml
echo "=== generated manifests-cluster.yaml redis lines ==="
grep -nE 'CLUSTER_NODES|REDISCLUSTER|REDIS_HOST|REDIS_PORT' /mnt/d/work/runtime-logs/manifests-cluster.yaml
