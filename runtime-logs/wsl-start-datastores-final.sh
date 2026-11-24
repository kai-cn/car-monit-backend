#!/usr/bin/env bash
# @description 启动 WSL 本地实测所需的 MySQL、Redis、PostgreSQL 与 Elasticsearch，并等待端口就绪。
# @author Tencent Hunyuan Hy
# @date 2026-11-24 12:20:00
# @usage bash runtime-logs/wsl-start-datastores-final.sh
# @dependencies Docker；新别名 mysql8.0/redis7/pg16/es7，兼容旧别名。
# NOTE: ES JVM 堆 350m、容器内存 700m，由用户调整；本脚本创建容器时沿用该配置。
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=runtime-logs/wsl-container-alias.sh
source "$HERE/wsl-container-alias.sh"

start_or_create() {
  local name="$1" image="$2" spec="$3"
  if docker ps --format '{{.Names}}' | grep -qx "$name"; then
    echo "$name RUNNING"
  elif docker ps -a --format '{{.Names}}' | grep -qx "$name"; then
    docker start "$name" >/dev/null 2>&1 && echo "$name STARTED" || echo "$name START_FAILED"
  else
    eval "docker run -d --name '$name' $spec '$image' >/dev/null 2>&1" && echo "$name CREATED" || echo "$name CREATE_FAILED"
  fi
}

start_or_create "$MYSQL_CONTAINER" mysql:8.0.30 "-e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=carmonitdb -p 3307:3306"
if (echo > /dev/tcp/127.0.0.1/6379) >/dev/null 2>&1; then
  echo "$REDIS_CONTAINER HOST_RUNNING"
else
  start_or_create "$REDIS_CONTAINER" redis:7-alpine "-p 6379:6379"
fi
start_or_create "$PG_CONTAINER" postgres:16-alpine "-e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=RuoYi -p 5432:5432"
start_or_create "$ES_CONTAINER" docker.elastic.co/elasticsearch/elasticsearch:7.17.13 "-e discovery.type=single-node -e ES_JAVA_OPTS=-Xms350m -Xmx350m --memory=700m -p 9200:9200 -p 9300:9300"

for i in $(seq 1 90); do
  docker exec "$MYSQL_CONTAINER" mysql -uroot -proot -e 'select 1' >/dev/null 2>&1 && break
  sleep 2
done
for i in $(seq 1 30); do
  (echo > /dev/tcp/127.0.0.1/6379) >/dev/null 2>&1 && break
  sleep 1
done
for i in $(seq 1 60); do
  docker exec "$PG_CONTAINER" pg_isready -U postgres -d RuoYi >/dev/null 2>&1 && break
  sleep 2
done
for i in $(seq 1 90); do
  curl -s --max-time 2 http://127.0.0.1:9200 >/dev/null 2>&1 && break
  sleep 2
done

echo "=== status ==="
docker ps --format '{{.Names}}|{{.Status}}|{{.Ports}}' | grep -E "$MYSQL_CONTAINER|$REDIS_CONTAINER|$PG_CONTAINER|$ES_CONTAINER" || true
