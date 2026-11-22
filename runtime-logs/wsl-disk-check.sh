#!/usr/bin/env bash
# @description 历史脚本 wsl-disk-check.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash wsl-disk-check.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Purpose: check WSL filesystem capacity for local packaging.
# Idea: report disk usage for root and Windows mount, plus target jar size.
# Risk: read-only.
df -h / /mnt/d | head -5
ls -lh /mnt/d/work/IdeaProjects/_local-package-20261122-130307/backend__master/ruoyi-admin/target/*.jar 2>/dev/null
