#!/bin/bash

# @description 历史脚本 dump_backend_seed.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash dump_backend_seed.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Print a file section for diagnosis.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Dump backend (carmonitdb) schema + limited seed rows for cloud parity verification.

set -uo pipefail

MY_PASS=$(docker exec mysql_wsl env 2>/dev/null | sed -n 's/^[^=]*MYSQL_ROOT_PASSWORD=//p' | tr -d '\r' | head -1)

[ -z "$MY_PASS" ] && { echo "no mysql pass"; exit 1; }

OUTDIR=/mnt/d/work/runtime-logs/backend-ddl

mkdir -p "$OUTDIR"



# Full schema for backend (84 tables, no data) already exists in repo; here we export schema

# + capped seed rows for a handful of core tables that endpoints read.

echo "=== full schema (structure) ==="

docker exec mysql_wsl sh -c "mysqldump -uroot -p'$MY_PASS' --no-tablespaces --no-data --skip-add-locks --skip-comments carmonitdb 2>/dev/null" > "$OUTDIR/schema_carmonitdb.sql"

echo "schema size=$(stat -c %s "$OUTDIR/schema_carmonitdb.sql")"



echo "=== seed rows (capped) for core tables ==="

TABLES="sys_user sys_role sys_menu sys_dept sys_dict_type sys_dict_data sys_config sys_user_role sys_role_menu base_gantry base_tollstation base_section base_vehicle"

OUT="$OUTDIR/seed_carmonitdb.sql"

{

  echo "SET NAMES utf8mb4;"

  echo "SET FOREIGN_KEY_CHECKS=0;"

  for t in $TABLES; do

    rowcnt=$(docker exec mysql_wsl sh -c "mysql -uroot -p'$MY_PASS' -N -e \"select count(*) from carmonitdb.$t\" 2>/dev/null")

    [ -z "$rowcnt" ] && { echo "-- skip $t (missing)"; continue; }

    echo "-- $t rows=$rowcnt"

    docker exec mysql_wsl sh -c "mysqldump -uroot -p'$MY_PASS' --no-tablespaces --no-create-info --skip-add-locks --skip-comments --where='1=1 LIMIT 200' carmonitdb $t 2>/dev/null"

  done

  echo "SET FOREIGN_KEY_CHECKS=1;"

} > "$OUT"

echo "seed size=$(stat -c %s "$OUT")"

grep -c 'INSERT INTO' "$OUT" || true

