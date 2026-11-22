#!/bin/bash

# @description 历史脚本 dump_schema.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash dump_schema.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Print a file section for diagnosis.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Dump schema-only + small seed for jl_data01 & minor schemas of openGauss RuoYi.

set -uo pipefail

GS_PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -1)

export PGPASSWORD="$GS_PASS"

OUT=/mnt/d/work/runtime-logs/ddl

mkdir -p "$OUT"



pg_dump -h 127.0.0.1 -p 5432 -U gaussdb -d RuoYi \

  --schema-only --no-owner --no-privileges \

  -n jl_data01 -n public \

  -T 'jl_data01.gen_table*' -T 'jl_data01.qrtz_*' \

  -f "$OUT/schema_jl_data01.sql" 2>"$OUT/dump.err"

echo "schema dump exit=$? size=$(stat -c %s "$OUT/schema_jl_data01.sql" 2>/dev/null || echo 0)"

head -3 "$OUT/dump.err" 2>/dev/null

wc -l "$OUT/schema_jl_data01.sql" 2>/dev/null

