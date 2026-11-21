#!/usr/bin/env bash
# 启动 car-monit-cpp（Linux/macOS）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

MODE="${1:-release}"
PORT="${CM_SERVER_PORT:-9989}"
CONFIG_DIR="${CM_CONFIG_DIR:-$ROOT/config}"
BUILD_DIR="$ROOT/build"

need() { command -v "$1" >/dev/null 2>&1 || { echo "缺少依赖: $1" >&2; exit 1; }; }
need cmake
need c++

echo "==> 检查依赖 (OpenSSL / zlib / pthread)"
if command -v pkg-config >/dev/null 2>&1; then
  pkg-config --exists openssl || echo "警告: 未找到 OpenSSL 开发包 (libssl-dev / openssl-devel)"
  pkg-config --exists zlib    || echo "警告: 未找到 zlib 开发包 (zlib1g-dev / zlib-devel)"
fi

BUILD_TYPE="Release"
[ "$MODE" = "debug" ] && BUILD_TYPE="Debug"

echo "==> 配置 ($BUILD_TYPE)"
cmake -S "$ROOT" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE="$BUILD_TYPE"

echo "==> 编译"
cmake --build "$BUILD_DIR" -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)"

if [ "${SKIP_TESTS:-0}" != "1" ]; then
  echo "==> 单元测试"
  "$BUILD_DIR/carmonit_tests"
fi

if [ "${SKIP_DEPS_CHECK:-0}" != "1" ]; then
  echo "==> 检查 MySQL(3307) / Redis(6379)"
  (exec 3<>/dev/tcp/127.0.0.1/3307) 2>/dev/null && echo "  MySQL 可连接" || echo "  警告: MySQL 127.0.0.1:3307 不可连接（登录等接口会失败）"
  (exec 3<>/dev/tcp/127.0.0.1/6379) 2>/dev/null && echo "  Redis 可连接" || echo "  警告: Redis 127.0.0.1:6379 不可连接（token/验证码接口会失败）"
fi

echo "==> 启动: http://0.0.0.0:$PORT"
exec "$BUILD_DIR/car-monit-cpp" --config "$CONFIG_DIR"
