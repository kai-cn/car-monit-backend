#!/usr/bin/env bash

# @description 历史脚本 failover-test.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash failover-test.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 测试 Redis Cluster 主从故障转移：停 1 主，验证副本提升，再恢复

echo ">>> 停 master 7000"

systemctl stop redis-cluster@7000

sleep 8

echo ">>> 7001 视角集群节点:"

redis-cli -p 7001 cluster nodes | awk '{print $1,$3,$4}'

echo ">>> 7005 角色(故障转移后应为 master):"

redis-cli -p 7005 cluster nodes | grep myself

echo ">>> 集群状态:"

redis-cli -p 7001 cluster info | grep -E 'cluster_state|cluster_size'

echo ">>> 恢复 7000"

systemctl start redis-cluster@7000

sleep 8

echo ">>> 7000 重新加入后的角色(应为 slave):"

redis-cli -p 7000 cluster nodes | grep myself

echo ">>> 最终集群状态:"

redis-cli -p 7000 cluster info | grep -E 'cluster_state|cluster_slots_ok'

