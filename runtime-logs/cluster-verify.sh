#!/usr/bin/env bash
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
