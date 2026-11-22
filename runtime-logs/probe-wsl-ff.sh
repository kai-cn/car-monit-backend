#!/usr/bin/env bash

# @description 历史脚本 probe-wsl-ff.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash probe-wsl-ff.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Diagnose why a WSL fast-forward failed (ahead/behind counts + git error).

d=/home/dev/IdeaProjects/car-monit-api-jdk21

br=$(git -C "$d" rev-parse --abbrev-ref HEAD)

echo "branch=$br"

git -C "$d" rev-list --left-right --count "origin/$br...HEAD"

git -C "$d" merge --ff-only "origin/$br" 2>&1 | head -20

echo "status:"

git -C "$d" status --short | head -10

