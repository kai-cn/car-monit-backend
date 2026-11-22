#!/usr/bin/env bash

# @description 历史脚本 probe-git-both-sides.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash probe-git-both-sides.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

echo "========== WSL IdeaProjects git 状态 =========="

for d in /home/dev/IdeaProjects/car-monit-*; do

  [[ -d "$d" ]] || continue

  name=$(basename "$d")

  printf '%-42s ' "$name"

  if [[ -f "$d/.git" ]]; then

    printf 'gitfile->%s' "$(sed -n 's/^gitdir: //p' "$d/.git")"

  elif [[ -d "$d/.git" ]]; then

    br=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null || echo GIT_ERROR)

    printf 'DIR branch=%s' "$br"

  else

    printf 'NO_GIT'

  fi

  echo

done

echo "========== Windows 侧 git 状态 =========="

for d in /mnt/d/work/IdeaProjects/car-monit-*; do

  [[ -d "$d/.git" || -f "$d/.git" ]] || continue

  br=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null || echo GIT_ERROR)

  printf '%-52s %s\n' "$(basename "$d")" "$br"

done

