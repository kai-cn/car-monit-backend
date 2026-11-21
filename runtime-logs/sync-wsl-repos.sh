#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Synchronize local and remote branches/worktrees; skips dirty user work.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Synchronize WSL standalone git repos with their fetched origin refs.
# Requires core.quotePath=false and core.autocrlf=false (Windows/WSL line-ending noise).
# Untracked files are preserved; dirty tracked worktrees are skipped.
for d in /home/dev/IdeaProjects/car-monit-*; do
  [ -d "$d/.git" ] || continue
  name=$(basename "$d")
  git -C "$d" config core.quotePath false
  git -C "$d" config core.autocrlf false
  br=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
  [ -n "$br" ] || { echo "SKIP no-branch $name"; continue; }
  dirty=$(git -C "$d" -c core.quotePath=false status --porcelain 2>/dev/null | grep -v '^??' | wc -l)
  if [ "$dirty" -gt 0 ]; then echo "SKIP dirty $name ($dirty)"; continue; fi
  git -C "$d" fetch origin --prune >/dev/null 2>&1 || { echo "FAIL fetch $name"; continue; }
  ref="origin/$br"
  git -C "$d" rev-parse --verify --quiet "$ref" >/dev/null || { echo "SKIP no-ref $name $br"; continue; }
  counts=$(git -C "$d" rev-list --left-right --count "$ref...HEAD" 2>/dev/null)
  behind=${counts%%[[:space:]]*}; ahead=${counts##*[[:space:]]}
  if [ "$behind" = "0" ]; then echo "OK $name ahead=$ahead"; continue; fi
  if [ "$ahead" = "0" ]; then
    git -C "$d" merge --ff-only "$ref" >/dev/null 2>&1 && echo "FF $name behind=$behind" || echo "FAIL ff $name"
  else
    git -C "$d" merge -X theirs "$ref" -m 'merge remote workflow optimization' >/dev/null 2>&1 && echo "MERGE $name behind=$behind ahead=$ahead" || echo "FAIL merge $name"
  fi
done
