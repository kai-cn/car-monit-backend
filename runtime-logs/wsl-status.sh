#!/usr/bin/env bash

# @description 历史脚本 wsl-status.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash wsl-status.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Read-only branch/dirty inventory for WSL car-monit-* repositories.

for d in /home/dev/IdeaProjects/car-monit-*; do

  [ -d "$d/.git" ] || continue

  b=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null)

  s=$(git -C "$d" status --porcelain 2>/dev/null | wc -l)

  printf '%-42s branch=%-34s dirty=%s\n' "$(basename "$d")" "$b" "$s"

done

