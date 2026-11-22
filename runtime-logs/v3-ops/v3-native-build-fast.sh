#!/usr/bin/env bash

# @description 历史脚本 v3-native-build-fast.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash v3-native-build-fast.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Native-image matrix helper; see docs/v3/final-jdk-matrix-verification-20261116.md.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Experimental native build: apply native-flink-exclude in both reactor stages and skip the

# second `clean`. Saves ~2% wall time; only safe when all sources were freshly compiled in stage 1.

# Experimental fast path: identical to v3-native-build-linux.sh but avoids the

# second `clean` by applying native-flink-exclude in BOTH reactor stages.

set -euo pipefail

APP="${1:-}"; JDK="${2:-}"; PROJ="${3:-}"; LABEL="${4:-x}"

MANDREL_HOME="${MANDREL_HOME:-/home/dev/tools/mandrel-25}"

MVN="${MVN:-/home/dev/.cache/ci-toolchain/apache-maven-3.9.9/bin/mvn}"

MAVEN_REPO="${MAVEN_REPO:-/home/dev/.m2/repository}"

EV=/mnt/d/work/runtime-logs/v3-ops/evidence

mkdir -p "$EV"

exec > >(tee "$EV/native-$LABEL.log") 2>&1

MOD=pro-business-api

[[ "$APP" == backend ]] && MOD=ruoyi-admin

export JAVA_HOME="$MANDREL_HOME"

export PATH="$MANDREL_HOME/bin:$PATH"

export MAVEN_OPTS="-Xmx2g -XX:+UseSerialGC"



echo "==== FAST native build label=$LABEL project=$PROJ ===="

cd "$PROJ"

echo "[1/2] install with native-flink-exclude"

"$MVN" -B -ntp -DskipTests -Dmaven.repo.local="$MAVEN_REPO" \

  clean install -Pnative-flink-exclude -pl "$MOD" -am

echo "[2/2] native:compile WITHOUT clean"

T0=$(date +%s)

"$MVN" -B -ntp -Pnative,native-flink-exclude -DskipTests -Dmaven.repo.local="$MAVEN_REPO" \

  -pl "$MOD" native:compile

T1=$(date +%s)

BIN="$PROJ/$MOD/target/$MOD"

[[ "$APP" == api ]] && BIN="$PROJ/$MOD/target/pro-business-api"

file "$BIN"

echo "binary_bytes=$(stat -c %s "$BIN")"

echo "native_compile_seconds=$((T1-T0))"

echo "FAST_BUILD_OK label=$LABEL"

