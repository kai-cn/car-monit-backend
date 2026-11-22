#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：launch-boot4-native-builds.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
# Sequential Mandrel25 native builds for Boot4 jdk21/jdk17 (api + backend).
# Usage: launch-boot4-native-builds.sh <index>
#   index 1: api-jdk21, 2: api-jdk17, 3: backend-jdk21, 4: backend-jdk17
set -euo pipefail
ROOT=/mnt/d/work/IdeaProjects
OPS=$ROOT/car-monit-api-java-V3/scripts/v3/ops
LOGDIR=/mnt/d/work/runtime-logs/v3-ops
IDX="${1:-1}"
case "$IDX" in
  1) APP=api;   JDK=21; REPO=car-monit-api-jdk21;    LABEL=api-boot4-jdk21-mandrel25-r1 ;;
  2) APP=api;   JDK=17; REPO=car-monit-api-jdk17;    LABEL=api-boot4-jdk17-mandrel25-r1 ;;
  3) APP=backend; JDK=21; REPO=car-monit-backend-jdk21; LABEL=backend-boot4-jdk21-mandrel25-r1 ;;
  4) APP=backend; JDK=17; REPO=car-monit-backend-jdk17; LABEL=backend-boot4-jdk17-mandrel25-r1 ;;
  *) echo "invalid index $IDX" >&2; exit 2 ;;
esac
LOG=$LOGDIR/$LABEL-launch.log
setsid env MANDREL_HOME=/home/dev/tools/mandrel-25 \
  bash "$OPS/v3-native-build-linux.sh" "$APP" "$JDK" "$ROOT/$REPO" "$LABEL" \
  >"$LOG" 2>&1 < /dev/null &
echo "launched $LABEL pid=$! log=$LOG"
