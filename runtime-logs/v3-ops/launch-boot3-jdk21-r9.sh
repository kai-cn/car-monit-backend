#!/usr/bin/env bash
# @description 历史脚本 launch-boot3-jdk21-r9.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash launch-boot3-jdk21-r9.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Fully detached launcher for Boot3 jdk21 native rebuild (r9).
OPS=/mnt/d/work/IdeaProjects/car-monit-api-java-V3/scripts/v3/ops
LOG=/mnt/d/work/runtime-logs/v3-ops/r9-launch.log
STARTED=/mnt/d/work/runtime-logs/v3-ops/r9-launch.started
rm -f "$STARTED"
setsid env MANDREL_HOME=/home/dev/tools/mandrel-21 \
  bash "$OPS/v3-native-build-linux.sh" api 21 \
  /mnt/d/work/IdeaProjects/car-monit-api-jdk21 api-boot3-jdk21-linux-r9 \
  >"$LOG" 2>&1 < /dev/null &
echo "launched pid=$!" >"$STARTED"
cat "$STARTED"
