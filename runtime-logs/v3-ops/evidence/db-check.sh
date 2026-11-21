#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：db-check.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
# Verify the app's datasource target exists and the credentials work.
set -u
PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -n 1)
echo "password_length=${#PASS}"
BIN=/usr/local/opengauss/bin

echo "=== list databases ==="
docker exec -e PGPASSWORD="$PASS" opengauss sh -c "$BIN/gsql -U gaussdb -d postgres -t -c 'select datname from pg_database' 2>&1 | head -n 20" || true

echo "=== select 1 on RuoYi ==="
docker exec -e PGPASSWORD="$PASS" opengauss sh -c "$BIN/gsql -U gaussdb -d RuoYi -t -c 'select 1' 2>&1 | head -n 5" || true

echo "=== table count in RuoYi ==="
docker exec -e PGPASSWORD="$PASS" opengauss sh -c "$BIN/gsql -U gaussdb -d RuoYi -t -c \"select count(*) from information_schema.tables where table_schema='public'\" 2>&1 | head -n 5" || true
