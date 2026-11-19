#!/bin/bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Print a file section for diagnosis.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Dump plate_color dictionary tables from local mysql_wsl (carmonitdb) for cloud seeding.
set -uo pipefail
MY_PASS=$(docker exec mysql_wsl env 2>/dev/null | sed -n 's/^[^=]*MYSQL_ROOT_PASSWORD=//p' | tr -d '\r' | head -1)
echo "mysql pass present: $([ -n "$MY_PASS" ] && echo yes || echo no)"
OUT=/mnt/d/work/runtime-logs/ddl/mysql_dict.sql
{
  echo "-- minimal carmonitdb dict seed for api plate_color"
  echo "CREATE DATABASE IF NOT EXISTS carmonitdb;"
  echo "USE carmonitdb;"
  for t in sys_dict_type sys_dict_data; do
    docker exec mysql_wsl sh -c "mysqldump -uroot -p'$MY_PASS' --no-tablespaces --skip-add-locks --skip-comments carmonitdb $t 2>/dev/null"
  done
} > "$OUT"
echo "size=$(stat -c %s "$OUT")"
wc -l "$OUT"
echo "=== plate_color rows ==="
docker exec mysql_wsl sh -c "mysql -uroot -p'$MY_PASS' -N -e \"select count(*) from carmonitdb.sys_dict_data d join carmonitdb.sys_dict_type t on d.dict_type=t.dict_type where d.dict_type like 'plate%'\" 2>/dev/null"
docker exec mysql_wsl sh -c "mysql -uroot -p'$MY_PASS' -N -e \"select dict_type, dict_label, dict_value from carmonitdb.sys_dict_data where dict_type like 'plate%' limit 8\" 2>/dev/null"
