#!/usr/bin/env bash

# @description 历史脚本 probe-wsl-projects.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash probe-wsl-projects.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

for r in car-monit-api-jdk21 car-monit-api-jdk17 car-monit-backend-jdk21 car-monit-backend-jdk17; do

  d=/home/dev/IdeaProjects/$r

  echo "=== $r ==="

  git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null

  git -C "$d" status --short 2>/dev/null | head -12

done

