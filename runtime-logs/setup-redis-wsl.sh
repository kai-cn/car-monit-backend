#!/usr/bin/env bash

# @description 历史脚本 setup-redis-wsl.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash setup-redis-wsl.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Write GitHub Secrets or local configuration from runtime-supplied values only.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 在 WSL(openEuler) 部署 Redis 8.10.3：单节点(6379) + 6 节点 Cluster(7000-7005)

# 供 k3d 集群 backend/api 共享缓存。按 k3s-remediation-plan.md R3 执行。

# 偏差（已记录）：未启用 requirepass（本地开发集群，仅在私有 WSL 桥接网段，不做认证）；

#                 单节点沿用已验证可达的桥接地址 172.18.0.1。

set -euo pipefail

REDIS_BIN=/opt/redis-8.10.3/bin

BASE=/srv/redis

SINGLE_PORT=6379

CLUSTER_PORTS=(7000 7001 7002 7003 7004 7005)



echo "=== 1) 链接二进制到 /usr/local/bin ==="

for b in redis-server redis-cli redis-sentinel redis-benchmark redis-check-rdb redis-check-aof; do

  ln -sf "$REDIS_BIN/$b" /usr/local/bin/$b

done

"$REDIS_BIN/redis-server" --version



echo "=== 2) 目录 ==="

mkdir -p "$BASE"/{etc,data,logs,run,data/single,data/cluster}

for p in "${CLUSTER_PORTS[@]}"; do mkdir -p "$BASE/data/cluster/$p"; done



echo "=== 3) 单节点配置文件 $BASE/etc/redis-single.conf ==="

cat > "$BASE/etc/redis-single.conf" <<'CONF'

port 6379

bind 0.0.0.0

protected-mode no

dir /srv/redis/data/single

maxmemory 256mb

maxmemory-policy allkeys-lru

appendonly yes

appendfsync everysec

save 900 1

save 300 10

daemonize no

pidfile /srv/redis/run/redis-single.pid

logfile /srv/redis/logs/redis-single.log

CONF



echo "=== 4) 6 节点 Cluster 配置 ==="

for p in "${CLUSTER_PORTS[@]}"; do

cat > "$BASE/etc/redis-cluster-$p.conf" <<CONF

port $p

bind 0.0.0.0

protected-mode no

dir /srv/redis/data/cluster/$p

cluster-enabled yes

cluster-config-file nodes-$p.conf

cluster-node-timeout 5000

cluster-announce-ip 172.18.0.1

cluster-announce-port $p

cluster-announce-bus-port 1$p

maxmemory 64mb

appendonly yes

appendfsync everysec

daemonize no

pidfile /srv/redis/run/redis-cluster-$p.pid

logfile /srv/redis/logs/redis-cluster-$p.log

CONF

done



echo "=== 5) systemd unit: redis-single ==="

cat > /etc/systemd/system/redis-single.service <<'UNIT'

[Unit]

Description=Redis 8.10.3 single node (k3d shared cache)

After=network.target



[Service]

Type=simple

ExecStart=/opt/redis-8.10.3/bin/redis-server /srv/redis/etc/redis-single.conf

Restart=always

LimitNOFILE=65535



[Install]

WantedBy=multi-user.target

UNIT



echo "=== 6) systemd unit: redis-cluster@ (模板) ==="

cat > /etc/systemd/system/redis-cluster@.service <<'UNIT'

[Unit]

Description=Redis 8.10.3 cluster node %i (k3d shared cache)

After=network.target



[Service]

Type=simple

ExecStart=/opt/redis-8.10.3/bin/redis-server /srv/redis/etc/redis-cluster-%i.conf

Restart=always

LimitNOFILE=65535



[Install]

WantedBy=multi-user.target

UNIT



echo "=== 7) 停掉旧的 redis6380，启用单节点 ==="

systemctl daemon-reload

systemctl disable --now redis6380 2>/dev/null || true

systemctl enable --now redis-single

sleep 2

echo "single status: $(systemctl is-active redis-single)"

"$REDIS_BIN/redis-cli" -p 6379 ping

echo "单节点配置完成。Cluster 用: systemctl enable --now redis-cluster@{7000..7005}"

