#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
files=""
for d in car-monit-backend-jdk17 car-monit-backend-jdk21 car-monit-backend-jdk25 car-monit-backend-java-V3 \
         car-monit-api-java-V3 car-monit-api-jdk17 car-monit-api-jdk21 car-monit-api-jdk25; do
  f="/mnt/d/work/IdeaProjects/$d/.github/workflows/self-hosted-ci.yml"
  files="$files $f"
  echo "== $d"
  grep -E 'JAVA_MAJOR:|BASE_IMAGE:|branches:' "$f" | sed 's/^[[:space:]]*//'
  if grep -q '__JAVA_MAJOR__\|__BRANCHES__' "$f"; then echo "  !! LEFTOVER PLACEHOLDER"; fi
done
echo "=== YAML validate ==="
python3 /mnt/d/work/runtime-logs/validate-yaml.py $files
