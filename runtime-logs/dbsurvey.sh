#!/bin/bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -uo pipefail
GS_PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -1)
export PGPASSWORD="$GS_PASS"
echo "=== schemas ==="
psql -h 127.0.0.1 -p 5432 -U gaussdb -d RuoYi -Atc "select nspname from pg_namespace where nspname not like 'pg_%' and nspname<>'information_schema'" 2>&1 | head -20
echo "=== table counts per schema ==="
psql -h 127.0.0.1 -p 5432 -U gaussdb -d RuoYi -Atc "select table_schema, count(*) from information_schema.tables group by 1 order by 2 desc" 2>&1 | head -20
echo "=== jl_data01 tables (if any) ==="
psql -h 127.0.0.1 -p 5432 -U gaussdb -d RuoYi -Atc "select table_name from information_schema.tables where table_schema='jl_data01' order by 1" 2>&1 | head -60
echo "=== row counts of key tables ==="
for t in ods_lwzxsfsj_fee_records_01 ods_szdn_gantry ods_szdn_toll ods_rt_szdn_snapshot_flow_addcode zdata_trail_fitting; do
  cnt=$(psql -h 127.0.0.1 -p 5432 -U gaussdb -d RuoYi -Atc "select count(*) from jl_data01.$t" 2>/dev/null)
  echo "  $t = ${cnt:-ERR}"
done
