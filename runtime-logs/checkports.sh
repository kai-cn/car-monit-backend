#!/bin/bash

# @description 历史脚本 checkports.sh：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash checkports.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Check that required local service ports are available before starting a service.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

for p in 5432 3307 6379; do

  (echo > /dev/tcp/127.0.0.1/$p) >/dev/null 2>&1 && echo "port $p OPEN" || echo "port $p CLOSED"

done

