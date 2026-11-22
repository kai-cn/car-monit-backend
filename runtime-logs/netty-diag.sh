#!/usr/bin/env bash

# @description 历史脚本 netty-diag.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash netty-diag.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

echo "=== backend log: netty/unsafe/direct memory ==="

docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=300 2>&1 | grep -E 'ByteBufAllocator|ExceptionInInitializerError|Unsafe|direct buffer|Direct buffer|OutOfMemoryError|NoClassDefFoundError|Fontconfig|Caused by' | head -20

echo "=== api log: same ==="

docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-api --tail=200 2>&1 | grep -E 'ByteBufAllocator|ExceptionInInitializerError|Unsafe|Direct buffer|OutOfMemoryError|NoClassDefFoundError|Caused by' | head -12

