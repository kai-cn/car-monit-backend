#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo '=== processes ==='
ps -eo pid,etime,args | grep -E 'compare-native-jvm|python3' | grep -v grep | cut -c1-180
echo '=== artifacts ==='
ls -lh /mnt/d/work/runtime-logs/v3-ops/evidence/compare-api-jdk25-ab-20261116-150757.* 2>/dev/null
echo '=== json ==='
cat /mnt/d/work/runtime-logs/v3-ops/evidence/compare-api-jdk25-ab-20261116-150757.json 2>/dev/null
echo '=== log tail ==='
tail -n 5 /mnt/d/work/runtime-logs/v3-ops/jdk25-ab-launch.log
