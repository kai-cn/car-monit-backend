#!/usr/bin/env bash
# @description 历史脚本 cluster-verify.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash cluster-verify.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 验证 Redis Cluster 状态与跨槽读写
redis-cli -p 7000 cluster info | grep -E 'cluster_state|cluster_slots'
redis-cli -c -p 7000 set foo bar >/dev/null
redis-cli -c -p 7000 set baz qux >/dev/null
echo "foo=$(redis-cli -c -p 7000 get foo)"
echo "baz=$(redis-cli -c -p 7000 get baz)"
echo "=== cluster nodes (id role) ==="
redis-cli -p 7000 cluster nodes | awk '{print $1, $3, $4}'
