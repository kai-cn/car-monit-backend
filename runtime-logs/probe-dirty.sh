#!/usr/bin/env bash
# @description 历史脚本 probe-dirty.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash probe-dirty.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Show the first dirty path and its index/worktree attributes (diagnostic only).
cd /home/dev/IdeaProjects/car-monit-api-jdk25 || exit 1
f=$(git status --porcelain | head -1 | sed 's/^...//')
echo "FILE=[$f]"
git hash-object "$f"
git rev-parse ":$f"
git config --get core.autocrlf
git check-attr text eol -- "$f"
file "$f"
