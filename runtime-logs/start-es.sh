#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 在 WSL 启动 Elasticsearch 7.17.13（单节点，400M 内存限制），监听 172.18.0.1:9200
set -e
sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" > /etc/sysctl.d/99-es.conf
docker run -d --name es-wsl --memory=400m --restart=unless-stopped \
  -p 172.18.0.1:9200:9200 -p 172.18.0.1:9300:9300 \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms200m -Xmx200m" \
  -e "xpack.security.enabled=false" \
  -e "bootstrap.memory_lock=false" \
  docker.elastic.co/elasticsearch/elasticsearch:7.17.13
echo "=== waiting for ES ==="
for i in $(seq 1 30); do
  if curl -s -m 3 http://172.18.0.1:9200 >/dev/null 2>&1; then echo "ES UP after ${i}x3s"; break; fi
  sleep 3
done
curl -s -m 5 http://172.18.0.1:9200 | head -c 400
echo
