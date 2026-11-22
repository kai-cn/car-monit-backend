#!/usr/bin/env bash
# @description 历史脚本 wsl-local-evidence.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash wsl-local-evidence.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Purpose: inspect WSL local service retest evidence.
# Idea: print contract summary and load metrics with safe quoting inside a script.
# Risk: read-only.
echo "=== contract ==="
grep -E 'Test run finished|tests found|tests successful|tests failed' /home/dev/local-retest/contract.log 2>/dev/null | tail -8 || true
echo "=== load json ==="
cat /home/dev/local-retest/junit-load.json 2>/dev/null | head -30 || true
echo "=== load report ==="
grep -E 'Test run finished|tests found|tests successful|tests failed' /home/dev/local-retest/load.log 2>/dev/null | tail -8 || true
