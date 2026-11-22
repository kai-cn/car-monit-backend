#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== node taints ==="
for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do
  echo -n "$n: "
  docker exec k3d-v3-server-0 kubectl describe node "$n" 2>/dev/null | grep -i '^Taints:' | head -1
done
echo "=== tools in WSL VM ==="
for c in curl wget jq tar docker k3d redis-server; do printf "%s: " "$c"; command -v "$c" || echo missing; done
echo "=== start cluster-shared redis on 6380 ==="
if ! (echo > /dev/tcp/127.0.0.1/6380) 2>/dev/null; then
  redis-server --bind 0.0.0.0 --port 6380 --daemonize yes --save '' --appendonly no --maxmemory 64mb --maxmemory-policy allkeys-lru
  echo "redis-server started"
else
  echo "6380 already listening"
fi
sleep 1
redis-cli -h 127.0.0.1 -p 6380 ping 2>&1 || true
echo "=== reachability from k3d server node ==="
for hp in 172.18.0.1:3307 172.18.0.1:5432 172.18.0.1:6380; do
  out=$(docker exec k3d-v3-server-0 wget -S --spider -T 2 "http://$hp/" 2>&1 | head -2 | tr '\n' ' ')
  echo "$hp => $out"
done
