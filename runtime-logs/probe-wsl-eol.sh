#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Diagnose WSL line-ending drift: compares worktree/index/HEAD blob hashes for one file.
cd /home/dev/IdeaProjects/car-monit-api-jdk25
git config --list --show-origin | grep -E 'autocrlf|eol|safecrlf' || true
echo "worktree=$(git hash-object .dockerignore)"
echo "index=$(git rev-parse :.dockerignore)"
echo "head=$(git rev-parse HEAD:.dockerignore)"
file .dockerignore
