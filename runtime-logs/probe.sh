#!/usr/bin/env bash
# @description 历史脚本 probe.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash probe.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== demo deployments ==="
docker exec k3d-v3-server-0 kubectl get deploy -o wide 2>&1 | head -10
echo "=== demo images ==="
for d in v3-ci-probe v3-api-ci-probe; do
  docker exec k3d-v3-server-0 kubectl get deploy "$d" -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}' 2>&1
done
echo "=== WSL host ips ==="
hostname -I
ip route show default 2>/dev/null | head -2
ip -4 addr show eth0 2>/dev/null | grep inet || true
echo "=== k3d network ==="
docker network inspect k3d-v3 --format '{{range .IPAM.Config}}{{.Subnet}} gw={{.Gateway}}{{end}}' 2>/dev/null
echo "=== memory ==="
free -h | head -3
echo "=== tcp reachability from WSL VM ==="
for hp in 127.0.0.1:3307 127.0.0.1:5432 172.29.16.1:6379 172.29.16.1:9200 172.29.16.1:9092; do
  h=${hp%%:*}; p=${hp##*:}
  if timeout 3 bash -c "echo > /dev/tcp/$h/$p" 2>/dev/null; then echo "$h:$p OK"; else echo "$h:$p FAIL"; fi
done
echo "=== tcp reachability from k3d node container ==="
for hp in 172.18.0.1:3307 172.18.0.1:5432 172.29.16.1:6379 172.29.16.1:9200 172.29.16.1:9092; do
  h=${hp%%:*}; p=${hp##*:}
  if docker exec k3d-v3-server-0 timeout 3 bash -c "echo > /dev/tcp/$h/$p" 2>/dev/null; then echo "$h:$p OK"; else echo "$h:$p FAIL"; fi
done
