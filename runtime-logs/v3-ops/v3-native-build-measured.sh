#!/usr/bin/env bash

# @description 历史脚本 v3-native-build-measured.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash v3-native-build-measured.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# LEGACY-SCRIPT-ANNOTATION

# 文件：v3-native-build-measured.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

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

