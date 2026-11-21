#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Show the first dirty path and its index/worktree attributes (diagnostic only).
cd /home/dev/IdeaProjects/car-monit-api-jdk25 || exit 1
f=$(git status --porcelain | head -1 | sed 's/^...//')
echo "FILE=[$f]"
git hash-object "$f"
git rev-parse ":$f"
git config --get core.autocrlf
git check-attr text eol -- "$f"
file "$f"
