#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Fully detached launcher for Boot3 jdk21 native rebuild (r9).
OPS=/mnt/d/work/IdeaProjects/car-monit-api-java-V3/scripts/v3/ops
LOG=/mnt/d/work/runtime-logs/v3-ops/r9-launch.log
STARTED=/mnt/d/work/runtime-logs/v3-ops/r9-launch.started
rm -f "$STARTED"
setsid env MANDREL_HOME=/home/dev/tools/mandrel-21 \
  bash "$OPS/v3-native-build-linux.sh" api 21 \
  /mnt/d/work/IdeaProjects/car-monit-api-jdk21 api-boot3-jdk21-linux-r9 \
  >"$LOG" 2>&1 < /dev/null &
echo "launched pid=$!" >"$STARTED"
cat "$STARTED"
