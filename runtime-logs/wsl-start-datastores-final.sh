#!/usr/bin/env bash
# @description 启动 WSL 本地实测所需的 MySQL、Redis、PostgreSQL 与 Elasticsearch，并等待端口就绪。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 05:15:00
# @usage bash runtime-logs/wsl-start-datastores-final.sh
# @dependencies Docker；已有容器 mysql_wsl/redis_wsl/pg_wsl/es-wsl 或对应镜像。
set -uo pipefail

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

start_or_create mysql_wsl mysql:8.0.30 "-e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=carmonitdb -p 3307:3306"
# NOTE: WSL 宿主可能已有 redis-server 占用 6379；此时复用宿主服务，避免容器端口冲突。
if (echo > /dev/tcp/127.0.0.1/6379) >/dev/null 2>&1; then
  echo "redis HOST_RUNNING"
else
  start_or_create redis_wsl redis:7-alpine "-p 6379:6379"
fi
start_or_create pg_wsl postgres:16-alpine "-e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=RuoYi -p 5432:5432"
start_or_create es-wsl docker.elastic.co/elasticsearch/elasticsearch:7.17.13 "-e discovery.type=single-node -e ES_JAVA_OPTS=-Xms512m -Xmx512m -p 9200:9200 -p 9300:9300"

for i in $(seq 1 90); do
  docker exec mysql_wsl mysql -uroot -proot -e 'select 1' >/dev/null 2>&1 && break
  sleep 2
done
for i in $(seq 1 30); do
  (echo > /dev/tcp/127.0.0.1/6379) >/dev/null 2>&1 && break
  sleep 1
done
for i in $(seq 1 60); do
  docker exec pg_wsl pg_isready -U postgres -d RuoYi >/dev/null 2>&1 && break
  sleep 2
done
for i in $(seq 1 90); do
  curl -s --max-time 2 http://127.0.0.1:9200 >/dev/null 2>&1 && break
  sleep 2
done

echo "=== status ==="
docker ps --format '{{.Names}}|{{.Status}}|{{.Ports}}' | grep -E 'mysql_wsl|redis_wsl|pg_wsl|es-wsl' || true
