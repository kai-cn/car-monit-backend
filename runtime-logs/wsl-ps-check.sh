#!/usr/bin/env bash
# @description 历史脚本 wsl-ps-check.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash wsl-ps-check.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Purpose: check whether local package resume process is still running.
# Idea: simple ps filter; no modification.
# Risk: read-only.
ps -ef | grep -E 'wsl-local-package-resume|mvn|java' | grep -v grep | head -30
