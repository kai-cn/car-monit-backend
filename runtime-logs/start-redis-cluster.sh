#!/usr/bin/env bash
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
