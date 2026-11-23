#!/usr/bin/env bash
# @description 从 WSL backend master 当前源码重建 jar，落地所有 body.code 非 200 修复。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 07:38:02
# @usage bash runtime-logs/rebuild-current-backend-master.sh
# @dependencies WSL master、JDK8、Maven。
set -euo pipefail
SRC=/home/dev/IdeaProjects/car-monit-backend
DST=/home/dev/local-package/backend-master
LOG=/mnt/d/work/runtime-logs/rebuild-current-backend-master.log
rm -rf "$DST"
mkdir -p "$DST"
cp -a "$SRC"/. "$DST"/
cd "$DST"
JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.502.b07-1.oe2403sp4.x86_64
JAVA_HOME="$JAVA_HOME" PATH="$JAVA_HOME/bin:$PATH" \
  mvn -B -ntp -DskipTests -Dspring-boot.aot.skip=true -pl ruoyi-admin -am clean package > "$LOG" 2>&1
echo "BUILD_OK $(stat -c %s "$DST/ruoyi-admin/target/ruoyi-admin.jar") $(date '+%Y-%m-%d %H:%M:%S')"
