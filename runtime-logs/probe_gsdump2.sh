#!/usr/bin/env bash
set -u
C=opengauss
D=/usr/local/opengauss/bin/gs_dump
L=/usr/local/opengauss/lib

echo '=== gs_dump usage (first 30 lines) ==='
docker exec -u 70 -e LD_LIBRARY_PATH="$L" "$C" "$D" --help 2>&1 | head -30

try() {
  local tag="$1"; shift
  echo "--- TRY $tag ---"
  docker exec -u 70 -e LD_LIBRARY_PATH="$L" "$C" "$@" > /tmp/pd.sql 2>/tmp/pd.err
  local rc=$?
  echo "rc=$rc size=$(wc -c < /tmp/pd.sql 2>/dev/null)"
  head -6 /tmp/pd.err
  if [ "$rc" = 0 ] && [ -s /tmp/pd.sql ]; then
    echo "SUCCESS: $tag"; head -6 /tmp/pd.sql; return 0
  fi
  return 1
}

echo '=== positional-db attempts ==='
try "positional-RuoYi-fp" "$D" RuoYi -Fp --no-owner -f /tmp/pd_out.sql
try "positional-postgres-fp" "$D" postgres -Fp --no-owner -f /tmp/pd_out.sql
try "positional-RuoYi-plain-stdout" "$D" RuoYi -Fp --no-owner
echo '=== check file from -f runs ==='
docker exec -u 70 -e LD_LIBRARY_PATH="$L" "$C" bash -c 'wc -c /tmp/pd_out.sql 2>/dev/null; head -5 /tmp/pd_out.sql 2>/dev/null'
