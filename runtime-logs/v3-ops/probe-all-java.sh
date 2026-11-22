#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
ps -eo pid,etime,rss,comm,args | grep -Ei 'java|native' | grep -v grep | cut -c1-220
echo '=== memory ==='
free -m | head -2
echo '=== r9 log size ==='
stat -c '%s %y' /mnt/d/work/runtime-logs/v3-ops/evidence/native-api-boot3-jdk21-linux-r9.log
