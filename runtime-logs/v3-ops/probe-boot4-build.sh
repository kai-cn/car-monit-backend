#!/usr/bin/env bash

# @description 历史脚本 probe-boot4-build.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash probe-boot4-build.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

LABEL=${1:-api-boot4-jdk21-mandrel25-r1}

echo "=== processes ==="

ps -eo pid,etime,rss,args | grep -E 'v3-native-build-linux|native-image|com.oracle.svm' | grep -v grep | cut -c1-180

echo "=== log tail ==="

tail -n 16 "/mnt/d/work/runtime-logs/v3-ops/evidence/native-$LABEL.log" 2>/dev/null

echo "=== binary ==="

case "$LABEL" in

  api*) B=/mnt/d/work/IdeaProjects/car-monit-api-jdk21/pro-business-api/target/pro-business-api ;;

  backend*) B=/mnt/d/work/IdeaProjects/car-monit-backend-jdk21/ruoyi-admin/target/ruoyi-admin ;;

esac

ls -lh "$B" 2>/dev/null || echo NONE

