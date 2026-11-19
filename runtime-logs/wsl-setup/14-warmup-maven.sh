#!/usr/bin/env bash
set -u
LOG=/tmp/maven-warmup.log
echo "start $(date -Is)" > "$LOG"
cd /mnt/d/work/IdeaProjects/car-monit-backend-java-V3 || exit 1
runuser -u dev -- env HOME=/home/dev mvn -B -q -DskipTests \
  -pl ruoyi-common,ruoyi-system,ruoyi-framework,ruoyi-admin -am compile >> "$LOG" 2>&1
echo "COMPILE_RC=$? $(date -Is)" >> "$LOG"
runuser -u dev -- env HOME=/home/dev mvn -B -q \
  -pl ruoyi-common,ruoyi-system -am test >> "$LOG" 2>&1
echo "TEST_RC=$? $(date -Is)" >> "$LOG"
echo "done" >> "$LOG"
touch /tmp/maven-warmup.done
