#!/usr/bin/env bash
# @description 历史脚本 sync-wsl-repos2.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash sync-wsl-repos2.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Synchronize local and remote branches/worktrees; skips dirty user work.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Second-pass WSL sync: removes untracked native-image hint files that became tracked
# on the remote branch, then repeats the fast-forward/merge logic of sync-wsl-repos.sh.
for d in /home/dev/IdeaProjects/car-monit-*; do
  [ -d "$d/.git" ] || continue
  name=$(basename "$d")
  git -C "$d" config core.quotePath false
  git -C "$d" config core.autocrlf false
  br=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
  [ -n "$br" ] || continue
  dirty=$(git -C "$d" status --porcelain | grep -v '^??' | wc -l)
  if [ "$dirty" -gt 0 ]; then echo "SKIP dirty $name ($dirty)"; continue; fi
  # remove untracked native hints that are now tracked on remote
  for rel in \
    pro-business-api/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json \
    ruoyi-admin/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json; do
    if [ -f "$d/$rel" ] && git -C "$d" ls-files --error-unmatch "$rel" >/dev/null 2>&1; then :; elif [ -f "$d/$rel" ]; then rm -f "$d/$rel"; fi
  done
  git -C "$d" fetch origin --prune >/dev/null 2>&1 || continue
  ref="origin/$br"
  counts=$(git -C "$d" rev-list --left-right --count "$ref...HEAD" 2>/dev/null)
  behind=${counts%%[[:space:]]*}; ahead=${counts##*[[:space:]]}
  if [ "$behind" = "0" ]; then echo "OK $name ahead=$ahead"; continue; fi
  if [ "$ahead" = "0" ]; then
    git -C "$d" merge --ff-only "$ref" >/dev/null 2>&1 && echo "FF $name" || echo "FAIL ff $name"
  else
    git -C "$d" merge -X theirs "$ref" -m 'merge remote workflow optimization' >/dev/null 2>&1 && echo "MERGE $name" || echo "FAIL merge $name"
  fi
done
