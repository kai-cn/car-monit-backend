#!/usr/bin/env bash

# @description 历史脚本 reset-wsl-worktrees.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash reset-wsl-worktrees.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Restore WSL working trees from the git index using NUL-safe path iteration.

# Used only to normalize CRLF/LF drift introduced by copying from Windows; does not touch untracked files.

for d in /home/dev/IdeaProjects/car-monit-*; do

  [ -d "$d/.git" ] || continue

  git -C "$d" config core.quotePath false

  git -C "$d" config core.autocrlf false

  (cd "$d" && git ls-files -z | xargs -0 -r git checkout-index -f --) >/dev/null 2>&1

  n=$(git -C "$d" -c core.quotePath=false status --porcelain 2>/dev/null | grep -v '^??' | wc -l)

  echo "$(basename "$d") dirty=$n"

done

