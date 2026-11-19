#!/usr/bin/env bash
# 本地复现：验证 api 的 rust/cpp 分支源码可构建 + 制品生命周期演练。
# 前置：cargo/rustc 1.90+、cmake 3.20+、g++ 13、libpq-dev、libssl-dev、zlib1g-dev、ninja。
#       Python3（用于 GitHub API 下载 tarball）。
set -euo pipefail

TOK="${GH_TOKEN_OVERRIDE:-}"
if [ -z "$TOK" ]; then
  TOK="$(git -C /workspace/cbm remote get-url origin | sed -E 's#.*oauth2:([^@]+)@.*#\1#')"
fi
WORK="${WORK:-/tmp/api-rust-cpp-verify}"
REPO="kai-cn/car-monit-api"
mkdir -p "$WORK"

echo "==> 1. 下载 rust/cpp 分支 tarball"
curl -sL -u "oauth2:$TOK" "https://codeload.github.com/$REPO/tar.gz/refs/heads/car-monit-api-rust" -o "$WORK/rust.tgz"
curl -sL -u "oauth2:$TOK" "https://codeload.github.com/$REPO/tar.gz/refs/heads/car-monit-api-cpp" -o "$WORK/cpp.tgz"
tar -xzf "$WORK/rust.tgz" -C "$WORK" --wildcards '*/car-monit-api-rust/*'
tar -xzf "$WORK/cpp.tgz"  -C "$WORK" --wildcards '*/car-monit-api-cpp/*'
RUST_SRC="$(find "$WORK" -maxdepth 2 -type d -name car-monit-api-rust | head -1)"
CPP_SRC="$(find "$WORK" -maxdepth 2 -type d -name car-monit-api-cpp | head -1)"
echo "RUST_SRC=$RUST_SRC"; echo "CPP_SRC=$CPP_SRC"

echo "==> 2. 构建 Rust（cargo build --release --locked）"
( cd "$RUST_SRC" && rustup toolchain install 1.90.0 --profile minimal 2>/dev/null || true
  rustup default 1.90.0 2>/dev/null || true
  cargo build --release --locked )
file "$RUST_SRC/target/release/car-monit-api-rust"

echo "==> 3. Rust --check-config（用脱敏配置）"
sed -E 's#192\.168\.56\.10#<DB_HOST>#g' "$RUST_SRC/config/application.yaml" > /tmp/rust_app.yaml
"$RUST_SRC/target/release/car-monit-api-rust" --check-config --config /tmp/rust_app.yaml

echo "==> 4. 构建 C++（cmake -DCM_WITH_KAFKA=ON；OFF 路径源码有 bug，勿用）"
( cd "$CPP_SRC" && cmake -S . -B build-verify -DCMAKE_BUILD_TYPE=Release -DCM_WITH_KAFKA=ON \
    && cmake --build build-verify --parallel 4 )
file "$CPP_SRC/build-verify/car-monit-api"

echo "==> 5. 制品生命周期演练（install/uninstall，需已提交 deploy/standalone 改动）"
API=/workspace/cbm-api
T="$WORK/lifecycle"; rm -rf "$T"; mkdir -p "$T/root/payloads/rust/config" "$T/root/payloads/cpp/configs" \
  "$T/root/systemd" "$T/root/config" "$T/prefix" "$T/log" "$T/units"
cp "$RUST_SRC/target/release/car-monit-api-rust" "$T/root/payloads/rust/"
sed -E 's#192\.168\.56\.10#<DB_HOST>#g' "$RUST_SRC/config/application.yaml" > "$T/root/payloads/rust/config/application.yaml"
cp "$CPP_SRC/build-verify/car-monit-api" "$T/root/payloads/cpp/"
sed -E 's#192\.168\.56\.10#<DB_HOST>#g' "$CPP_SRC/configs/config.yaml" > "$T/root/payloads/cpp/configs/config.yaml"
cp "$API/deploy/standalone/install.sh" "$API/deploy/standalone/uninstall.sh" "$T/root/"
cp "$API/deploy/standalone/systemd/car-monit-api-rust.service" "$API/deploy/standalone/systemd/car-monit-api-cpp.service" "$T/root/systemd/"
for svc in rust cpp; do
  bash "$T/root/install.sh" --prefix "$T/prefix" --log-dir "$T/log" --unit-dir "$T/units" \
    --service "$svc" --user "$(id -un)" --no-start
  test -f "$T/units/car-monit-api-$svc.service"
  bash "$T/root/uninstall.sh" --prefix "$T/prefix" --log-dir "$T/log" --unit-dir "$T/units" \
    --service "$svc" --no-systemctl
  test ! -d "$T/prefix/$svc" && echo "==> $svc 生命周期 OK"
done
echo "==> ALL VERIFY PASSED"
