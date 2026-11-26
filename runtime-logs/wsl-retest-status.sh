#!/usr/bin/env bash
# @description 历史脚本 wsl-retest-status.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash wsl-retest-status.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Purpose: inspect WSL local service retest state.
# Idea: report process, output files, app log tail and port state.
# Risk: read-only.
echo PROCESSES
ps -ef | grep -E 'wsl-local-service-retest|ruoyi-admin.jar|junit-platform' | grep -v grep | head -20 || true
echo FILES
ls -lh /home/dev/wsl-service-retest 2>/dev/null | head -30 || true
echo APPLOG
tail -40 /home/dev/wsl-service-retest/app.log 2>/dev/null || true
echo PORT
ss -ltnp 2>/dev/null | grep 19903 || true
echo CONTAINERS
docker ps --format '{{.Names}}|{{.Ports}}' | head -20
