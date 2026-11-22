#!/usr/bin/env bash

# @description 历史脚本 probe-build-status.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash probe-build-status.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

echo '=== java/maven/native processes ==='

ps -eo pid,etime,rss,args | grep -E 'native-image|maven|v3-native-build-linux|launch-boot3' | grep -v grep

echo '=== r9 files ==='

ls -lh /mnt/d/work/runtime-logs/v3-ops/r9-launch.log /mnt/d/work/runtime-logs/v3-ops/evidence/native-api-boot3-jdk21-linux-r9.log 2>/dev/null

echo '=== r9 evidence tail ==='

tail -n 25 /mnt/d/work/runtime-logs/v3-ops/evidence/native-api-boot3-jdk21-linux-r9.log 2>/dev/null

echo '=== target binary ==='

ls -lh /mnt/d/work/IdeaProjects/car-monit-api-jdk21/pro-business-api/target/pro-business-api 2>/dev/null

