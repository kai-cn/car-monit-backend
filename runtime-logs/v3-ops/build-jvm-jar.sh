#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：build-jvm-jar.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
# Build the api fat jar with an explicit JDK, no native profile.
# Usage: build-jvm-jar.sh <worktree-dir> <jdk-home> <label>
set -u
REPO=${1:?worktree required}
JH=${2:?jdk home required}
LABEL=${3:?label required}
EVID=/mnt/d/work/runtime-logs/v3-ops/evidence
LOG="$EVID/jvm-build-$LABEL.log"
cd "$REPO" || exit 3
export JAVA_HOME="$JH"
export PATH="$JAVA_HOME/bin:$PATH"
echo "=== JVM build $LABEL ==="
date
"$JAVA_HOME/bin/java" -version 2>&1 | head -2
/home/dev/.cache/ci-toolchain/apache-maven-3.9.9/bin/mvn -B -ntp -DskipTests clean package -pl pro-business-api -am >"$LOG" 2>&1
RC=$?
tail -n 25 "$LOG"
echo "BUILD_RC=$RC log=$LOG"
exit $RC
