#!/usr/bin/env bash
# @description 历史脚本 check-fonts2.sh：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash check-fonts2.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== JDK lib/fonts ==="
ls -la /home/dev/.cache/ci-toolchain/jdk-25.0.5+8/lib/fonts 2>/dev/null | head -12
ls /home/dev/.cache/ci-toolchain/jdk-25.0.5+8/lib/fontconfig* 2>/dev/null | head -8
echo "=== base image fontconfig libs ==="
docker run --rm --entrypoint sh mysql:8.0.30 -c 'ldconfig -p 2>/dev/null | grep -i fontconfig | head -5; ls /usr/share/fontconfig 2>/dev/null | head -5; cat /etc/os-release | head -2'
echo "=== try java AWT font listing in built image ==="
docker run --rm --entrypoint sh car-monit-backend:local -c 'ls /opt/jdk/lib/fonts 2>/dev/null | head; /opt/jdk/bin/java -Dsun.java2d.fontconfig=/opt/jdk/lib/fontconfig.properties.src -Xmx32m -cp /app/app.jar -version 2>&1 | head -3' 2>&1 | head -12
