#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo '=== compare processes ==='
ps -eo pid,etime,rss,args | grep -E 'compare-native-jvm|jdk25-ab' | grep -v grep
echo '=== ab log ==='
ls -lh /mnt/d/work/runtime-logs/v3-ops/jdk25-ab-launch.log
tail -n 30 /mnt/d/work/runtime-logs/v3-ops/jdk25-ab-launch.log
echo '=== compare artifacts ==='
ls -lh /mnt/d/work/runtime-logs/v3-ops/evidence/compare-api-jdk25-ab-* 2>/dev/null
