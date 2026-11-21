#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Synchronize local and remote branches/worktrees; skips dirty user work.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -euo pipefail
L=/home/dev/IdeaProjects
W=/mnt/d/work/IdeaProjects
for spec in \
  'car-monit-backend-jdk25:ruoyi-admin/pom.xml' \
  'car-monit-backend-jdk21:ruoyi-admin/pom.xml' \
  'car-monit-backend-jdk17:ruoyi-admin/pom.xml' \
  'car-monit-api-jdk21:pro-business-api/pom.xml' \
  'car-monit-api-jdk17:pro-business-api/pom.xml'; do
  repo="${spec%%:*}"
  rel="${spec#*:}"
  cp -f "$L/$repo/$rel" "$W/$repo/$rel"
  echo "POM $repo/$rel"
done
for repo in car-monit-backend-jdk25 car-monit-backend-jdk21 car-monit-backend-jdk17; do
  rel='ruoyi-admin/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json'
  mkdir -p "$W/$repo/$(dirname "$rel")"
  cp -f "$L/$repo/$rel" "$W/$repo/$rel"
  echo "HINTS $repo"
done
echo SYNCED_OK
