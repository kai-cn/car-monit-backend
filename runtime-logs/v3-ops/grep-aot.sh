#!/usr/bin/env bash
# @description 历史脚本 grep-aot.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash grep-aot.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Extract structured matches (paths/options) from long command lines or logs.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
grep -n -i 'process-aot\|aot' /mnt/d/work/runtime-logs/v3-ops/evidence/native-backend-jdk25-ext4-linuxmvn-r10.log | head -30
