#!/usr/bin/env bash
# @description 释放 5432 端口并启动 parity PostgreSQL 容器。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 08:10:00
# @usage bash runtime-logs/restore-local-pg.sh
# @dependencies docker。
set -uo pipefail
docker stop opengauss >/dev/null 2>&1 || true
docker stop pg_wsl >/dev/null 2>&1 || true
docker rm -f pg_wsl >/dev/null 2>&1 || true
docker rm -f pg >/dev/null 2>&1 || true

if docker ps -a --format '{{.Names}}' | grep -qx pgtest; then
  docker start pgtest >/dev/null 2>&1 || true
fi
if docker ps --format '{{.Names}}' | grep -qx pgtest && docker exec pgtest pg_isready -U postgres -d RuoYi >/dev/null 2>&1; then
  echo PGTEST_READY_55432
  docker port pgtest
  exit 0
fi

docker run -d --name pg_wsl -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=RuoYi -p 5432:5432 postgres:16-alpine >/dev/null
for _ in $(seq 1 60); do
  if docker exec pg_wsl pg_isready -U postgres -d RuoYi >/dev/null 2>&1; then
    echo PG_WSL_READY_5432
    docker port pg_wsl
    exit 0
  fi
  sleep 2
done
echo PG_TIMEOUT
docker ps -a --format '{{.Names}}|{{.Status}}|{{.Ports}}'
exit 1
