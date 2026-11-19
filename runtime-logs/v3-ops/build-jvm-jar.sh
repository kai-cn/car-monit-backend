#!/usr/bin/env bash
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
