#!/usr/bin/env bash
# @description 历史脚本 probe-wsl-eol.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash probe-wsl-eol.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Diagnose WSL line-ending drift: compares worktree/index/HEAD blob hashes for one file.
cd /home/dev/IdeaProjects/car-monit-api-jdk25
git config --list --show-origin | grep -E 'autocrlf|eol|safecrlf' || true
echo "worktree=$(git hash-object .dockerignore)"
echo "index=$(git rev-parse :.dockerignore)"
echo "head=$(git rev-parse HEAD:.dockerignore)"
file .dockerignore
