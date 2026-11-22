#!/bin/bash

# @description 历史脚本 run_perf_compare.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash run_perf_compare.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Run a build/verification command with a fixed environment and write evidence.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -uo pipefail

NATIVE="/mnt/d/work/runtime-logs/cicd-artifacts/native-api-jdk25-115MB/api-jdk25-linux-amd64.bin"

JAR="/mnt/d/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api-1.0.jar"

JAVA="/home/dev/tools/mandrel-25/bin/java"

export EVIDENCE_DIR=/mnt/d/work/runtime-logs/v3-ops/evidence

bash /mnt/d/work/IdeaProjects/car-monit-api-java-V3/scripts/v3/ops/v3-compare-native-jvm.sh \

  --native "$NATIVE" --jar "$JAR" --java "$JAVA" \

  --duration 60 --interval 5 --label api-jdk25-cloudnative-20261117 \

  2>&1 | tee /mnt/d/work/runtime-logs/perf-compare-20261117.log

