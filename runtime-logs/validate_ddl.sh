#!/bin/bash
# @description 历史脚本 validate_ddl.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash validate_ddl.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Validate generated DDL + seed load cleanly into vanilla postgres.
set -uo pipefail
export PGPASSWORD=test
echo "=== wait for pgtest ==="
for i in $(seq 1 30); do
  if psql -h 127.0.0.1 -p 55432 -U postgres -d RuoYi -Atc "select 1" >/dev/null 2>&1; then echo "ready after ${i}s"; break; fi
  sleep 1
done
echo "=== load schema ==="
psql -h 127.0.0.1 -p 55432 -U postgres -d RuoYi -v ON_ERROR_STOP=1 \
  -f /mnt/d/work/runtime-logs/ddl/schema_jl_data01.sql 2>&1 | tail -8
echo "schema_exit=${PIPESTATUS[0]}"
echo "=== load seed ==="
psql -h 127.0.0.1 -p 55432 -U postgres -d RuoYi -v ON_ERROR_STOP=1 \
  -f /mnt/d/work/runtime-logs/ddl/seed_jl_data01.sql 2>&1 | tail -8
echo "=== table + row verification ==="
psql -h 127.0.0.1 -p 55432 -U postgres -d RuoYi -Atc \
  "select 'tables='||count(*) from information_schema.tables where table_schema='jl_data01'"
for t in ods_lwzxsfsj_fee_records_01 ods_szdn_gantry ods_szdn_toll; do
  psql -h 127.0.0.1 -p 55432 -U postgres -d RuoYi -Atc "select '$t='||count(*) from jl_data01.$t"
done
