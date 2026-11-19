#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Read-only branch/dirty inventory for WSL car-monit-* repositories.
for d in /home/dev/IdeaProjects/car-monit-*; do
  [ -d "$d/.git" ] || continue
  b=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null)
  s=$(git -C "$d" status --porcelain 2>/dev/null | wc -l)
  printf '%-42s branch=%-34s dirty=%s\n' "$(basename "$d")" "$b" "$s"
done
