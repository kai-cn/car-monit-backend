#!/usr/bin/env bash

# @description 历史脚本 v3-native-build-fast-measured.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash v3-native-build-fast-measured.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Native-image matrix helper; see docs/v3/final-jdk-matrix-verification-20261116.md.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# /usr/bin/time -v wrapper for v3-native-build-fast.sh; writes resource-<label>.txt evidence.

set -euo pipefail

LABEL=$1

EV=/mnt/d/work/runtime-logs/v3-ops/evidence

mkdir -p "$EV"

T0=$(date +%s)

/usr/bin/time -v -o "$EV/resource-$LABEL.txt" env \

  MANDREL_HOME=/home/dev/tools/mandrel-25 \

  MVN=/home/dev/.cache/ci-toolchain/apache-maven-3.9.9/bin/mvn \

  MAVEN_REPO=/home/dev/.m2/repository \

  bash /mnt/d/work/runtime-logs/v3-ops/v3-native-build-fast.sh \

  api 21 /home/dev/IdeaProjects/car-monit-api-jdk21 "$LABEL"

T1=$(date +%s)

echo "FAST_MEASURED wall_seconds=$((T1-T0))"

grep -E 'Elapsed|Maximum resident|Percent of CPU' "$EV/resource-$LABEL.txt"

