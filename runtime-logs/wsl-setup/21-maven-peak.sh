#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：21-maven-peak.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set -u
LOG=/tmp/maven-peak.log
echo "start $(date -Is)" > "$LOG"
cd /mnt/d/work/IdeaProjects/car-monit-backend-java-V3 || exit 1
runuser -u dev -- env HOME=/home/dev mvn -B -q -DskipTests \
  -pl ruoyi-common,ruoyi-system,ruoyi-framework,ruoyi-admin -am compile >> "$LOG" 2>&1
echo "COMPILE_RC=$? $(date -Is)" >> "$LOG"
runuser -u dev -- env HOME=/home/dev mvn -B -q \
  -pl ruoyi-common,ruoyi-system -am test >> "$LOG" 2>&1
echo "TEST_RC=$? $(date -Is)" >> "$LOG"
echo "done" >> "$LOG"
touch /tmp/maven-peak.done
