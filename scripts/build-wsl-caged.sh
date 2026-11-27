#!/usr/bin/env bash
# @description 在 WSL 中编译 Go/Rust 双项目，用 systemd-run cgroup  cages 限制内存，
#              防止编译器瞬时占用超过 WSL 上限导致 WSL2 虚拟机被 Windows 宿主回收。
#              WSL 上限由 ~/.wslconfig 的 memory=10GB 决定；本脚本把单路编译内存上限
#              设为 10G（与 WSL 上限一致），线程数保留 512 以免 Go 编译器 newosproc 失败。
# @author Tencent Hunyuan Hy
# @date 2026-11-27 10:17:47
# @usage bash scripts/build-wsl-caged.sh [go|rust|all]
#        go   - 仅编译 car-monit-go/cmd/server 到 bin/carmonit-server
#        rust - 仅编译 car-monit-rust 到 target/debug/car-monit-rust
#        all  - 依次编译两者（默认）
# @dependencies sudo、systemd-run（systemd 249+）、dev 用户的 Go 1.27.4 与 Rust 1.100.0 工具链

set -euo pipefail

MEMORY_MAX="10G"
TASKS_MAX="512"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-all}"

run_caged() {
  local unit="$1"; shift
  # NOTE: 非 root 无法创建 transient scope，必须用 sudo；-p User=dev 保证 HOME 指向
  #       dev 的模块缓存，否则 Go/Rust 会重新下载依赖并可能因网络失败。
  sudo systemctl reset-failed "${unit}.scope" 2>/dev/null || true
  sudo systemd-run --scope \
    -p "MemoryMax=${MEMORY_MAX}" \
    -p "TasksMax=${TASKS_MAX}" \
    -p User=dev \
    --unit="${unit}" \
    env HOME=/home/dev "$@"
}

case "$TARGET" in
  go|all)
    echo "[build] Go 1.27.4 -> ${ROOT}/car-monit-go/bin/carmonit-server"
    (cd "${ROOT}/car-monit-go" && run_caged build-go \
      GOMAXPROCS=1 GOPROXY=off \
      /usr/local/go/bin/go build -p=1 -buildvcs=false -trimpath \
        -o bin/carmonit-server ./cmd/server)
    ;;
esac

case "$TARGET" in
  rust|all)
    echo "[build] Rust 1.100.0 -> ${ROOT}/car-monit-rust/target/debug/car-monit-rust"
    (cd "${ROOT}/car-monit-rust" && run_caged build-rust \
      CARGO_BUILD_JOBS=1 CARGO_HOME=/home/dev/.cargo RUSTUP_HOME=/home/dev/.rustup \
      PATH=/home/dev/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
      /home/dev/.cargo/bin/cargo build)
    ;;
esac

echo "[build] 完成: ${TARGET}"
