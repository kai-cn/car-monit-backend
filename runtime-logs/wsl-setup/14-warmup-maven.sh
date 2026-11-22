#!/usr/bin/env bash
# @description 历史脚本 14-warmup-maven.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash 14-warmup-maven.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# LEGACY-SCRIPT-ANNOTATION
# 文件：14-warmup-maven.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set -u
LOG=/tmp/maven-warmup.log
echo "start $(date -Is)" > "$LOG"
cd /mnt/d/work/IdeaProjects/car-monit-backend-java-V3 || exit 1
runuser -u dev -- env HOME=/home/dev mvn -B -q -DskipTests \
  -pl ruoyi-common,ruoyi-system,ruoyi-framework,ruoyi-admin -am compile >> "$LOG" 2>&1
echo "COMPILE_RC=$? $(date -Is)" >> "$LOG"
runuser -u dev -- env HOME=/home/dev mvn -B -q \
  -pl ruoyi-common,ruoyi-system -am test >> "$LOG" 2>&1
echo "TEST_RC=$? $(date -Is)" >> "$LOG"
echo "done" >> "$LOG"
touch /tmp/maven-warmup.done
