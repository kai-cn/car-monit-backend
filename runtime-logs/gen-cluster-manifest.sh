#!/usr/bin/env bash

# @description 历史脚本 gen-cluster-manifest.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash gen-cluster-manifest.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
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

