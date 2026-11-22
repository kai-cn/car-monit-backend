#!/usr/bin/env bash
# @description 历史脚本 fix-wsl-git.sh：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash fix-wsl-git.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Convert copied worktrees with Windows-style .git pointer files into standalone
# git repositories usable from WSL (IDEA can open them directly).
set -uo pipefail
PTR_DIR=/mnt/d/work/runtime-logs/v3-ops/git-pointers
mkdir -p "$PTR_DIR"

for d in /home/dev/IdeaProjects/car-monit-*; do
  [[ -f "$d/.git" ]] || continue
  name=$(basename "$d")
  ptr=$(sed -n 's/^gitdir: //p' "$d/.git")
  printf '%s\n' "$ptr" > "$PTR_DIR/$name.txt"

  # D:/work/IdeaProjects/<repo>/.git/worktrees/<wt>
  rel=${ptr#*IdeaProjects/}
  repo=${rel%%/*}
  wt=${rel##*/}
  main="/mnt/d/work/IdeaProjects/$repo"
  headfile="$main/.git/worktrees/$wt/HEAD"
  if [[ ! -f "$headfile" ]]; then
    echo "SKIP(no HEAD) $name $headfile"; continue
  fi
  head=$(cat "$headfile")
  if [[ "$head" == ref:* ]]; then
    branch=${head#ref: refs/heads/}
  else
    branch="detached-$wt"
  fi

  rm -f "$d/.git"
  if ! git -C "$d" init -q; then echo "FAIL init $name"; continue; fi
  git -C "$d" remote remove origin 2>/dev/null || true
  git -C "$d" remote add origin "$main"
  if ! git -C "$d" fetch -q origin; then echo "FAIL fetch $name"; continue; fi
  if git -C "$d" rev-parse --verify -q "origin/$branch" >/dev/null; then
    git -C "$d" symbolic-ref HEAD "refs/heads/$branch"
    git -C "$d" reset --mixed "origin/$branch" >/dev/null 2>&1
    echo "OK $name branch=$branch repo=$repo"
  elif [[ "$head" != ref:* ]]; then
    git -C "$d" symbolic-ref HEAD "refs/heads/$branch"
    git -C "$d" reset --mixed "$head" >/dev/null 2>&1
    echo "OK $name detached=$head"
  else
    echo "FAIL(no remote branch) $name branch=$branch"
  fi
done
