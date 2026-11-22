#!/usr/bin/env bash

# @description 历史脚本 check-synced.sh：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash check-synced.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

files=""

for d in car-monit-backend-jdk17 car-monit-backend-jdk21 car-monit-backend-jdk25 car-monit-backend-java-V3 \

         car-monit-api-java-V3 car-monit-api-jdk17 car-monit-api-jdk21 car-monit-api-jdk25; do

  f="/mnt/d/work/IdeaProjects/$d/.github/workflows/self-hosted-ci.yml"

  files="$files $f"

  echo "== $d"

  grep -E 'JAVA_MAJOR:|BASE_IMAGE:|branches:' "$f" | sed 's/^[[:space:]]*//'

  if grep -q '__JAVA_MAJOR__\|__BRANCHES__' "$f"; then echo "  !! LEFTOVER PLACEHOLDER"; fi

done

echo "=== YAML validate ==="

python3 /mnt/d/work/runtime-logs/validate-yaml.py $files

