#!/usr/bin/env bash
# @description 历史脚本 wsl-clean-retest.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash wsl-clean-retest.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Purpose: clean stale local retest processes before rerun.
# Idea: stop any process holding port 19903 and remove stale pid/log state.
# Risk: scoped to local retest process and files.
pkill -f 'ruoyi-admin.jar' 2>/dev/null || true
pkill -f 'wsl-local-service-retest3.sh' 2>/dev/null || true
rm -rf /home/dev/local-retest/app.pid /home/dev/local-retest/contract.log /home/dev/local-retest/load.log 2>/dev/null || true
echo CLEANED
