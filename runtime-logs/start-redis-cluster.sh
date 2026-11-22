#!/usr/bin/env bash
# @description 历史脚本 start-redis-cluster.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash start-redis-cluster.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 启动 6 个 Redis Cluster 节点(7000-7005) 并建立开机自启软链
for p in 7000 7001 7002 7003 7004 7005; do
  systemctl start redis-cluster@$p
  ln -sf /etc/systemd/system/redis-cluster@.service /etc/systemd/system/multi-user.target.wants/redis-cluster@$p.service
done
sleep 3
echo "=== pings ==="
for p in 7000 7001 7002 7003 7004 7005; do
  echo -n "$p: "; redis-cli -p $p ping
done
