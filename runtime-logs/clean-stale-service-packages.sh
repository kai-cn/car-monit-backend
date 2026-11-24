#!/usr/bin/env bash
# @description 服务代码修改后清理旧版本 jar 与可执行文件，避免本地复测误启动旧包。
# @author Tencent Hunyuan Hy
# @date 2026-11-24 12:15:00
# @usage bash runtime-logs/clean-stale-service-packages.sh [--all]
# @dependencies 本地工作树与 /home/dev/local-package；--all 时同时删除 target/build 输出目录。
# NOTE: 默认只删除已知可执行产物；--all 会清理 Maven/Cargo/CMake 产物目录，耗时更长但最彻底。
set -uo pipefail

B=/home/dev/IdeaProjects/car-monit-backend
A=/home/dev/IdeaProjects/car-monit-api
OUT=/home/dev/local-package/current-master
ALL=0
[ "${1:-}" = "--all" ] && ALL=1

echo "=== running service processes (cleanup does not kill them) ==="
ps -ef | grep -E 'ruoyi-admin.jar|pro-business-api-1.0.jar|car-monit-(go|api|cpp|rust)|uvicorn app.main:app' | grep -v grep || true

remove_file() {
  local f="$1"
  if [ -e "$f" ]; then
    rm -f "$f" && echo "REMOVED $f"
  fi
}

echo "=== remove packaged service binaries ==="
remove_file "$OUT/backend/ruoyi-admin.jar"
remove_file "$OUT/api/pro-business-api-1.0.jar"
remove_file "$B/car-monit-go/bin/car-monit-go"
remove_file "$B/car-monit-rust/target/release/car-monit-rust"
remove_file "$B/car-monit-cpp/build-local/car-monit-cpp"
remove_file "$A/car-monit-api-go/bin/car-monit-api"
remove_file "$A/car-monit-api-rust/target/release/car-monit-api-rust"
remove_file "$A/car-monit-api-cpp/build-linux-kafka/car-monit-api"

if [ "$ALL" -eq 1 ]; then
  echo "=== remove build output directories ==="
  for d in \
    "$B/ruoyi-admin/target" "$B/ruoyi-system/target" "$A/pro-business-api/target" \
    "$B/car-monit-go/bin" "$A/car-monit-api-go/bin" \
    "$B/car-monit-rust/target/release" "$A/car-monit-api-rust/target/release" \
    "$B/car-monit-cpp/build-local" "$A/car-monit-api-cpp/build-linux-kafka"; do
    [ -d "$d" ] && rm -rf "$d" && echo "REMOVED_DIR $d"
  done
fi

echo "CLEAN_DONE"
