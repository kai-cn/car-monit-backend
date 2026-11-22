#!/usr/bin/env bash

# @description 历史脚本 check-fontconfig-props.sh：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash check-fontconfig-props.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

echo "=== JDK fontconfig files ==="

ls /home/dev/.cache/ci-toolchain/jdk-25.0.5+8/lib/ | grep -i font || true

echo "=== default lucida mapping ==="

grep -E '^filename\.|\.ttf' /home/dev/.cache/ci-toolchain/jdk-25.0.5+8/lib/fontconfig.properties 2>/dev/null | head -15 || true

echo "=== libfontmanager deps in image ==="

docker run --rm --entrypoint sh car-monit-backend:local -c 'ldd /opt/jdk/lib/libfontmanager.so 2>&1 | grep -i "not found\|fontconfig" | head -8'

