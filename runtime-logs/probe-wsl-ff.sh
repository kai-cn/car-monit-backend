#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Diagnose why a WSL fast-forward failed (ahead/behind counts + git error).
d=/home/dev/IdeaProjects/car-monit-api-jdk21
br=$(git -C "$d" rev-parse --abbrev-ref HEAD)
echo "branch=$br"
git -C "$d" rev-list --left-right --count "origin/$br...HEAD"
git -C "$d" merge --ff-only "origin/$br" 2>&1 | head -20
echo "status:"
git -C "$d" status --short | head -10
