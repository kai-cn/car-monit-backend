#!/usr/bin/env bash
# @description 历史脚本 check-backend-log.sh：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash check-backend-log.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
F=${1:-/tmp/backend25-native8.log}
grep -E 'Started RuoYiApplication|Tomcat started|APPLICATION FAILED|Exception in thread|port\(s\)' "$F" | head -12
echo '---TAIL---'
tail -n 18 "$F"
