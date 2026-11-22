#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo '=== listening 19902/19903 ==='
ss -lntp 2>/dev/null | grep -E ':(19902|19903)\b' || echo NONE
echo '=== /proc/net/tcp hex 4DE6/4DE7 ==='
grep -Ei ':(4DE6|4DE7) ' /proc/net/tcp /proc/net/tcp6 2>/dev/null || echo NONE
