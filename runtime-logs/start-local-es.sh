#!/usr/bin/env bash
# @description 启动本机 ES 容器，修复 api 模糊查询上游 503。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 08:32:28
# @usage bash runtime-logs/start-local-es.sh
# @dependencies docker。
set -uo pipefail
if docker ps --format '{{.Names}}' | grep -qx es-wsl; then
  echo ES_RUNNING
  exit 0
fi
docker start es-wsl >/dev/null 2>&1 || true
for _ in $(seq 1 90); do
  if curl -sS --max-time 2 http://127.0.0.1:9200 >/dev/null 2>&1; then
    echo ES_READY
    curl -sS --max-time 2 http://127.0.0.1:9200 | head -5
    exit 0
  fi
  sleep 2
done
echo ES_TIMEOUT
docker ps -a --format '{{.Names}}|{{.Status}}|{{.Ports}}' | grep '^es-wsl' || true
exit 1
