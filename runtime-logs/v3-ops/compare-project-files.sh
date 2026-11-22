#!/usr/bin/env bash
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
