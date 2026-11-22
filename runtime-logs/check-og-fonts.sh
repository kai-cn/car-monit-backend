#!/usr/bin/env bash

# @description 历史脚本 check-og-fonts.sh：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash check-og-fonts.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

for img in enmotech/opengauss:3.0.0 registry.cn-hangzhou.aliyuncs.com/helowin/oracle_11g:latest; do

  echo "=== $img ==="

  docker run --rm --entrypoint sh "$img" -c 'command -v fc-list || echo no-fc-list; fc-list 2>/dev/null | head -3; find /usr/share/fonts -type f -iname "*.ttf" 2>/dev/null | head -3; ldconfig -p 2>/dev/null | grep -i libfontconfig | head -2; cat /etc/os-release 2>/dev/null | head -2' 2>&1 | head -12

done

