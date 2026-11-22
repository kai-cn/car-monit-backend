#!/usr/bin/env bash

# @description 历史脚本 probe-all-java.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash probe-all-java.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

ps -eo pid,etime,rss,comm,args | grep -Ei 'java|native' | grep -v grep | cut -c1-220

echo '=== memory ==='

free -m | head -2

echo '=== r9 log size ==='

stat -c '%s %y' /mnt/d/work/runtime-logs/v3-ops/evidence/native-api-boot3-jdk21-linux-r9.log

