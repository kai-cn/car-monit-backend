#!/usr/bin/env bash

# @description 历史脚本 stop-redis-cluster-default.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash stop-redis-cluster-default.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 默认单节点模式：停止 cluster 节点并移除其开机自启软链（切换脚本会按需启动）

for p in 7000 7001 7002 7003 7004 7005; do

  systemctl stop redis-cluster@$p 2>/dev/null || true

  rm -f /etc/systemd/system/multi-user.target.wants/redis-cluster@$p.service

done

systemctl daemon-reload

echo -n "redis-single: "; systemctl is-active redis-single

echo -n "single ping: "; redis-cli -p 6379 ping

echo -n "cluster 7000 (expect stopped): "; redis-cli -p 7000 ping 2>/dev/null || echo stopped

