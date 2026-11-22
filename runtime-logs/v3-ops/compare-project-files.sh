#!/usr/bin/env bash
# @description 历史脚本 compare-project-files.sh：对比基线/候选结果并产出报告；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash compare-project-files.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Compare two artifacts/branches/logs and emit a structured verdict.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Compare Windows worktree vs WSL copy for selected projects, ignoring build outputs.
set -u
for name in "$@"; do
  W="/mnt/d/work/IdeaProjects/$name"
  L="/home/dev/IdeaProjects/$name"
  echo "========== $name =========="
  git -C "$L" status --short 2>/dev/null | head -12
  diff -qr --exclude=.git --exclude=target --exclude=build --exclude=node_modules \
    --exclude=.idea --exclude=*.iml --exclude=.codebuddy --exclude=.mimocode \
    "$W" "$L" 2>/dev/null | head -40
done
