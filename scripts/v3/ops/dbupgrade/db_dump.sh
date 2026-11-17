#!/usr/bin/env bash
# ======================================================================
# 用途：从 old 侧容器做逻辑导出，供 new 侧容器还原（真正的版本迁移路径）。
# 调用：bash db_dump.sh <app:api|backend> <db:mysql|opengauss>
# 输出：out/<db>_dump.sql + out/<db>_dump.method.txt
# 说明：凭据只从 CI_DB_PASSWORD 读取；导出失败时写出空 dump，由 db_cell.sh 回退夹具。
# ======================================================================
set -uo pipefail
APP="${1:?app required}"
DB="${2:?db required}"
PW="${CI_DB_PASSWORD:?CI_DB_PASSWORD required}"
mkdir -p out
: > "out/${DB}_dump.sql"

if [ "$DB" = "mysql" ]; then
  if docker exec mysql-old mysqldump -uroot -p"$PW" \
       --single-transaction --routines --triggers --databases carmonitdb \
       > "out/${DB}_dump.sql" 2>/dev/null && [ -s "out/${DB}_dump.sql" ]; then
    echo "mysqldump(mysql:8.0 -> plain SQL)" > "out/${DB}_dump.method.txt"
  else
    : > "out/${DB}_dump.sql"
    echo "FAILED:mysqldump" > "out/${DB}_dump.method.txt"
  fi
else
  export PGPASSWORD="$PW"
  if pg_dump -h 127.0.0.1 -p 5432 -U omm -d RuoYi -Fp --no-owner --no-acl \
       > "out/${DB}_dump.sql" 2>/dev/null && [ -s "out/${DB}_dump.sql" ]; then
    echo "pg_dump(host client -> plain SQL, from enmotech/opengauss:3.0.0)" > "out/${DB}_dump.method.txt"
  else
    : > "out/${DB}_dump.sql"
    echo "FAILED:pg_dump; fallback to gs_dump in container" > "out/${DB}_dump.method.txt"
    docker exec opengauss-old bash -lc 'gs_dump -U omm -d RuoYi -Fp --no-owner' \
      > "out/${DB}_dump.sql" 2>/dev/null || : > "out/${DB}_dump.sql"
  fi
fi
echo "dump bytes: $(wc -c < "out/${DB}_dump.sql") method: $(cat "out/${DB}_dump.method.txt")"
