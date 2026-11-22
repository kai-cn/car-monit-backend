#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a generated configuration to local or remote branches.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -euo pipefail
ROOT=/mnt/d/work/IdeaProjects
OPS=$ROOT/car-monit-api-java-V3/scripts/v3/ops
HINTS=$ROOT/car-monit-api-jdk25/pro-business-api/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json

python3 "$OPS/v3-port-jdk25-native-config.py" \
  "$ROOT/car-monit-api-jdk21/pro-business-api/pom.xml" \
  "$ROOT/car-monit-api-jdk17/pro-business-api/pom.xml" \
  "$ROOT/car-monit-backend-jdk21/ruoyi-admin/pom.xml" \
  "$ROOT/car-monit-backend-jdk17/ruoyi-admin/pom.xml"

for spec in \
  "car-monit-api-jdk21:pro-business-api:com.ruoyi" \
  "car-monit-api-jdk17:pro-business-api:com.ruoyi" \
  "car-monit-backend-jdk21:ruoyi-admin:com.ruoyi" \
  "car-monit-backend-jdk17:ruoyi-admin:com.ruoyi"; do
  IFS=: read -r repo mod pkg <<< "$spec"
  d="$ROOT/$repo/$mod/src/main/resources/META-INF/native-image/$pkg/v3-native-hints"
  mkdir -p "$d"
  cp -f "$HINTS" "$d/reflect-config.json"
  echo "HINTS $d/reflect-config.json"
done

echo APPLIED_OK
