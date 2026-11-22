#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Synchronize local and remote branches/worktrees; skips dirty user work.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -euo pipefail
SRC=/mnt/d/work/IdeaProjects
DST=/home/dev/IdeaProjects

copy() {
  local rel="$1"
  mkdir -p "$DST/$(dirname "$rel")"
  cp -f "$SRC/$rel" "$DST/$rel"
  echo "SYNC $rel"
}

for repo in car-monit-api-jdk21 car-monit-api-jdk17; do
  copy "$repo/pom.xml"
  copy "$repo/pro-business-api/pom.xml"
  copy "$repo/pro-business-api/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json"
done
for repo in car-monit-backend-jdk21 car-monit-backend-jdk17; do
  copy "$repo/pom.xml"
  copy "$repo/ruoyi-admin/pom.xml"
  copy "$repo/ruoyi-admin/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json"
done
echo SYNC_OK
