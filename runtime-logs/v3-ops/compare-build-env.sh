#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Compare two artifacts/branches/logs and emit a structured verdict.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
for f in /mnt/d/work/runtime-logs/v3-ops/evidence/native-api-boot4-jdk21-mandrel25-r2.log /mnt/d/work/runtime-logs/v3-ops/evidence/native-api-jdk21-ext4-linuxmvn-r2.log; do
  echo "=== $f ==="
  grep -c 'graalvm reachability metadata repository for' "$f"
  grep -m1 'Downloaded GraalVM reachability' "$f"
  grep -m1 'native-maven-plugin' "$f"
done
