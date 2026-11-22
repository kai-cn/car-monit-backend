#!/usr/bin/env bash
# @description 历史脚本 launch-jdk25-ab.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash launch-jdk25-ab.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
OPS=/mnt/d/work/IdeaProjects/car-monit-api-java-V3/scripts/v3/ops
LOG=/mnt/d/work/runtime-logs/v3-ops/jdk25-ab-launch.log
MARK=/mnt/d/work/runtime-logs/v3-ops/jdk25-ab.started
rm -f "$MARK"
setsid env EVIDENCE_DIR=/mnt/d/work/runtime-logs/v3-ops/evidence \
  bash "$OPS/v3-compare-native-jvm.sh" \
  --native /mnt/d/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api \
  --jar    /mnt/d/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api-1.0.jar \
  --java   /home/dev/tools/mandrel-25/bin/java \
  --duration 120 --interval 5 --probe / --label api-jdk25-ab \
  >"$LOG" 2>&1 < /dev/null &
echo "launched pid=$!" >"$MARK"
cat "$MARK"
