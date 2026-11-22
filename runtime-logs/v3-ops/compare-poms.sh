#!/usr/bin/env bash

# @description 历史脚本 compare-poms.sh：对比基线/候选结果并产出报告；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash compare-poms.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Compare two artifacts/branches/logs and emit a structured verdict.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

for p in /home/dev/IdeaProjects/car-monit-api-jdk21/pro-business-api/pom.xml /mnt/d/work/IdeaProjects/car-monit-api-jdk21/pro-business-api/pom.xml; do

  echo "=== $p ==="

  grep -n -E 'metadataRepository|requiredVersion|1\.1\.14|1\.1\.18' "$p" | head -20

done

