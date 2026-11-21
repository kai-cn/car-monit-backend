#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：probe_gsdump.sh
# 用途：只读检查/诊断。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：通常只读；若脚本内有明确写操作以其自身说明为准。
# 本地诊断 gs_dump 在 openGauss 3.0 容器内的可用调用形式。
set -u
C=opengauss
G=/usr/local/opengauss/bin/gsql
D=/usr/local/opengauss/bin/gs_dump
L=/usr/local/opengauss/lib
PW="${CI_DB_PASSWORD:-unused}"

echo '=== databases ==='
docker exec -u 70 -e LD_LIBRARY_PATH="$L" "$C" "$G" -d postgres -Atc "select datname from pg_database" 2>&1 | head -20

echo '=== gs_dump path/version ==='
docker exec -u 70 -e LD_LIBRARY_PATH="$L" "$C" "$D" --version 2>&1 | head -3

try() {
  local tag="$1"; shift
  echo "--- TRY $tag ---"
  docker exec -u 70 -e LD_LIBRARY_PATH="$L" "$C" "$@" > /tmp/probe_dump.sql 2>/tmp/probe_dump.err
  local rc=$?
  echo "rc=$rc size=$(wc -c < /tmp/probe_dump.sql 2>/dev/null)"
  head -8 /tmp/probe_dump.err
  if [ "$rc" = 0 ] && [ -s /tmp/probe_dump.sql ]; then
    echo "SUCCESS: $tag"
    head -5 /tmp/probe_dump.sql
    return 0
  fi
  return 1
}

echo '=== gs_dump attempts (socket uid70) ==='
try "socket-default-RuoYi-fp" "$D" -d RuoYi -Fp --no-owner -f /tmp/probe_dump.sql
try "socket-default-ruoyi-fp" "$D" -d ruoyi -Fp --no-owner -f /tmp/probe_dump.sql
try "socket-h-slash-tmp" "$D" -h /tmp -d postgres -Fp --no-owner -f /tmp/probe_dump.sql
try "socket-named-RuoYi-se" "$D" -d RuoYi -Fp -E UTF8 --no-owner -f /tmp/probe_dump.sql
try "plain-stdout" "$D" -d postgres -Fp --no-owner
