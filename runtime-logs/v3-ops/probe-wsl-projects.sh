#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
for r in car-monit-api-jdk21 car-monit-api-jdk17 car-monit-backend-jdk21 car-monit-backend-jdk17; do
  d=/home/dev/IdeaProjects/$r
  echo "=== $r ==="
  git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null
  git -C "$d" status --short 2>/dev/null | head -12
done
