#!/usr/bin/env bash
# @description 导入 api parity 所需的 PostgreSQL schema 与种子数据。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 08:10:00
# @usage bash runtime-logs/load-local-pg-fixtures.sh
# @dependencies docker、api scripts/v3/ops/parity/sql。
set -uo pipefail
A=/home/dev/IdeaProjects/car-monit-api/scripts/v3/ops/parity/sql
docker exec -i pg_wsl psql -U postgres -d RuoYi -v ON_ERROR_STOP=0 < "$A/schema_jl_data01.sql" > /mnt/d/work/runtime-logs/load-local-pg-schema.log 2>&1
echo SCHEMA_RC=$?
if [ -f "$A/seed_jl_data01.sql.gz" ]; then
  gzip -dc "$A/seed_jl_data01.sql.gz" | docker exec -i pg_wsl psql -U postgres -d RuoYi -v ON_ERROR_STOP=0 > /mnt/d/work/runtime-logs/load-local-pg-seed.log 2>&1
  echo SEED_RC=$?
fi
docker exec pg_wsl psql -U postgres -d RuoYi -c "select count(*) from jl_data01.ods_rt_szdn_snapshot_flow_addcode;" 2>&1 | tail -5
