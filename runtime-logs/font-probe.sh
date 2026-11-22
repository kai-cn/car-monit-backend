#!/usr/bin/env bash

# @description 历史脚本 font-probe.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash font-probe.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

for img in car-monit-sys:local enmotech/opengauss:3.0.0 registry.cn-hangzhou.aliyuncs.com/helowin/oracle_11g:latest mysql:8.0.30; do

  echo "=== $img ==="

  docker run --rm --entrypoint sh "$img" -c 'ldconfig -p 2>/dev/null | grep -E "libfontconfig|libfreetype|libexpat" | head -5; ls /etc/fonts/fonts.conf 2>/dev/null || echo no-fonts-conf; find /usr/share/fonts -type f 2>/dev/null | head -3' 2>&1 | head -10

done

