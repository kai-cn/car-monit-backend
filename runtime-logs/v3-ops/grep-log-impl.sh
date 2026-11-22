#!/usr/bin/env bash

# @description 历史脚本 grep-log-impl.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash grep-log-impl.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Extract structured matches (paths/options) from long command lines or logs.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

python3 /mnt/d/work/runtime-logs/v3-ops/grep-classpath.py \

  /mnt/d/work/runtime-logs/v3-ops/evidence/native-backend-boot4-jdk21-mandrel25-r2.log \

  '(slf4j|log4j|logback)[^:]*\.jar' | sort -u

