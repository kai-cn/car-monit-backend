#!/usr/bin/env bash
# @description 启动与云端 parity workflow 一致的 PostgreSQL RuoYi 数据库容器。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 07:38:02
# @usage bash runtime-logs/start-local-pg.sh
# @dependencies docker。
set -uo pipefail
if docker ps --format '{{.Names}}' | grep -qx pg_wsl; then
  echo PG_RUNNING
elif docker ps -a --format '{{.Names}}' | grep -qx pg_wsl; then
  docker start pg_wsl >/dev/null
  echo PG_STARTED
else
  docker rm -f pg_wsl >/dev/null 2>&1 || true
  docker run -d --name pg_wsl -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=RuoYi -p 5432:5432 postgres:16-alpine >/dev/null
  echo PG_CREATED
fi
for _ in $(seq 1 60); do
  if docker exec pg_wsl pg_isready -U postgres -d RuoYi >/dev/null 2>&1; then
    echo PG_READY
    exit 0
  fi
  sleep 2
done
echo PG_TIMEOUT
exit 1
