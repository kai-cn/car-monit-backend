#!/usr/bin/env bash
# @description 兼容旧入口的 WSL 本地多语言对齐启动脚本，转发到当前统一 runner。
# @author Tencent Hunyuan Hy
# @date 2026-11-23
# @usage bash runtime-logs/start-local-parity.sh --app backend --lang java --out runtime-logs/local-parity-matrix/backend/java-final --start '<command>'
# @dependencies Python 3、runtime-logs/local-parity-runner.py。
# NOTE: 保留此入口是为了复现旧文档中的命令，实际参数解析与证据落盘均由 local-parity-runner.py 完成。
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$ROOT/local-parity-runner.py" "$@"
