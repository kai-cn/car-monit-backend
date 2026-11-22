#!/usr/bin/env bash
# @description 历史脚本 final-redis-check.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash final-redis-check.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== verify-login (reads captcha code from redis-single:6379) ==="
bash /mnt/d/work/runtime-logs/verify-login.sh
echo "=== redis-single clients AFTER captcha (expect >1) ==="
redis-cli -p 6379 info clients 2>/dev/null | grep connected_clients
echo "=== captcha keys in 6379 (expect >=1) ==="
redis-cli -p 6379 --scan --pattern 'captcha_codes:*' 2>/dev/null | wc -l
