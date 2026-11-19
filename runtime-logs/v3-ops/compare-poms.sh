#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Compare two artifacts/branches/logs and emit a structured verdict.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
for p in /home/dev/IdeaProjects/car-monit-api-jdk21/pro-business-api/pom.xml /mnt/d/work/IdeaProjects/car-monit-api-jdk21/pro-business-api/pom.xml; do
  echo "=== $p ==="
  grep -n -E 'metadataRepository|requiredVersion|1\.1\.14|1\.1\.18' "$p" | head -20
done
