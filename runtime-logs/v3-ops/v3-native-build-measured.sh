#!/usr/bin/env bash
# Build a native image in WSL/ext4 with the pinned Linux Maven and record wall/CPU/RSS via /usr/bin/time -v.
# Usage: v3-native-build-measured.sh <api|backend> <jdk> <repo-name> <label> [mandrel-version]
# Precondition: stop mysql_wsl/opengauss first; native-image needs >10 GB RAM in this 12 GB WSL VM.
# Run a native build entirely inside WSL/ext4 with the Linux Maven toolchain,
# recording wall time, peak RSS and CPU utilisation via /usr/bin/time -v.
#
#   v3-native-build-measured.sh <api|backend> <jdk> <repo-name> <label> [mandrel]
set -euo pipefail
APP=$1 JDK=$2 REPO=$3 LABEL=$4
MANDREL_VERSION=${5:-25}
ROOT=/home/dev/IdeaProjects
OPS=$ROOT/car-monit-api-java-V3/scripts/v3/ops
EV=/mnt/d/work/runtime-logs/v3-ops/evidence
RES=$EV/resource-$LABEL.txt

mkdir -p "$EV"
echo "==== measured native build ===="
echo "label     : $LABEL"
echo "project   : $ROOT/$REPO (ext4)"
echo "maven     : /home/dev/.cache/ci-toolchain/apache-maven-3.9.9/bin/mvn"
echo "mandrel   : /home/dev/tools/mandrel-$MANDREL_VERSION"
echo "resource  : $RES"
date -Is

T0=$(date +%s)
/usr/bin/time -v -o "$RES" env \
  MANDREL_HOME=/home/dev/tools/mandrel-$MANDREL_VERSION \
  MVN=/home/dev/.cache/ci-toolchain/apache-maven-3.9.9/bin/mvn \
  MAVEN_REPO=/home/dev/.m2/repository \
  bash "$OPS/v3-native-build-linux.sh" "$APP" "$JDK" "$ROOT/$REPO" "$LABEL"
RC=$?
T1=$(date +%s)
echo "MEASURED_RC=$RC wall_seconds=$((T1-T0))"
echo "---- resource summary ----"
grep -E 'Elapsed|User time|System time|Percent of CPU|Maximum resident' "$RES" 2>/dev/null || true
