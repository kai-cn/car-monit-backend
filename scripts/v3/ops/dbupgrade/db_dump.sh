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
  # 宿主 pg_dump 无法 sha256 认证 openGauss；用容器内 gs_dump。
  # 关键：openGauss gs_dump 用【位置参数】传库名，不支持 PostgreSQL 的 -d 选项；
  #       且 uid70 + socket 免密最可靠（TCP + -w 对 sha256 不可靠）。
  # 本地实测：gs_dump RuoYi -Fp --no-owner 输出 67MB / 909 objects 成功。
  DBNAME=$(cat "out/${DB}_dbname.txt" 2>/dev/null || echo RuoYi)
  ok=0
  for dbname in "$DBNAME" RuoYi ruoyi; do
    if docker exec -u 70 -e LD_LIBRARY_PATH=/usr/local/opengauss/lib \
         opengauss-old /usr/local/opengauss/bin/gs_dump \
         "$dbname" -Fp --no-owner -E UTF8 \
         > "out/${DB}_dump.sql" 2>/dev/null && [ -s "out/${DB}_dump.sql" ]; then
      ok=1
      echo "gs_dump(in-container, positional db=$dbname, uid70 socket, openGauss 3.0.0 -> plain SQL)" \
        > "out/${DB}_dump.method.txt"
      break
    fi
  done
  if [ "$ok" != 1 ]; then
    : > "out/${DB}_dump.sql"
    echo "FAILED:gs_dump(in-container, positional)" > "out/${DB}_dump.method.txt"
  fi
fi
echo "dump bytes: $(wc -c < "out/${DB}_dump.sql") method: $(cat "out/${DB}_dump.method.txt")"
