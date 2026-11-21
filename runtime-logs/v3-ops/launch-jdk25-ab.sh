#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
OPS=/mnt/d/work/IdeaProjects/car-monit-api-java-V3/scripts/v3/ops
LOG=/mnt/d/work/runtime-logs/v3-ops/jdk25-ab-launch.log
MARK=/mnt/d/work/runtime-logs/v3-ops/jdk25-ab.started
rm -f "$MARK"
setsid env EVIDENCE_DIR=/mnt/d/work/runtime-logs/v3-ops/evidence \
  bash "$OPS/v3-compare-native-jvm.sh" \
  --native /mnt/d/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api \
  --jar    /mnt/d/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api-1.0.jar \
  --java   /home/dev/tools/mandrel-25/bin/java \
  --duration 120 --interval 5 --probe / --label api-jdk25-ab \
  >"$LOG" 2>&1 < /dev/null &
echo "launched pid=$!" >"$MARK"
cat "$MARK"
