#!/usr/bin/env bash

# @description 历史脚本 check-flink-in-jar.sh：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash check-flink-in-jar.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

B=/home/dev/k3s-build

echo "=== flink libs in api.jar ==="

unzip -l "$B/api.jar" | awk '/BOOT-INF\/lib\/flink/ {print $1, $4}'

echo "=== flink libs in backend.jar ==="

unzip -l "$B/backend.jar" | awk '/BOOT-INF\/lib\/flink/ {print $1, $4}'

echo "=== platform-specific jars in both ==="

for j in api backend; do

  echo "--- $j ---"

  unzip -l "$B/$j.jar" | awk '{print $4}' | grep -E '^BOOT-INF/lib/.*(aarch_64|osx|windows)' || true

done

