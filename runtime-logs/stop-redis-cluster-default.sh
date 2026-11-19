#!/usr/bin/env bash
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
