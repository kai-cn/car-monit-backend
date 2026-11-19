#!/bin/bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Run a build/verification command with a fixed environment and write evidence.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -uo pipefail
NATIVE="/mnt/d/work/runtime-logs/cicd-artifacts/native-api-jdk25-115MB/api-jdk25-linux-amd64.bin"
JAR="/mnt/d/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api-1.0.jar"
JAVA="/home/dev/tools/mandrel-25/bin/java"
echo "native=$(stat -c %s "$NATIVE") jar=$(stat -c %s "$JAR")"
chmod +x "$NATIVE"
bash /mnt/d/work/runtime-logs/v3-ops/v3-compare-business.sh \
  --app api --native "$NATIVE" --jar "$JAR" --java "$JAVA" \
  --label api-jdk25-cloudnative-20261117 \
  2>&1 | tee /mnt/d/work/runtime-logs/business-compare-20261117.log
