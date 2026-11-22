#!/usr/bin/env bash

# @description 历史脚本 probe-ab-status.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash probe-ab-status.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

echo '=== compare processes ==='

ps -eo pid,etime,rss,args | grep -E 'compare-native-jvm|jdk25-ab' | grep -v grep

echo '=== ab log ==='

ls -lh /mnt/d/work/runtime-logs/v3-ops/jdk25-ab-launch.log

tail -n 30 /mnt/d/work/runtime-logs/v3-ops/jdk25-ab-launch.log

echo '=== compare artifacts ==='

ls -lh /mnt/d/work/runtime-logs/v3-ops/evidence/compare-api-jdk25-ab-* 2>/dev/null

