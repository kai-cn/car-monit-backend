#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：run-debug-db.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
# Run the JDK25 native binary with DEBUG logging on the datasource path only,
# so a failed connection reports the real driver error.
set -u
BIN=${1:-/mnt/d/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api}
PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -n 1)
echo "password_length=${#PASS}"

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$PASS"
export LOGGING_LEVEL_ORG_POSTGRESQL=DEBUG
export LOGGING_LEVEL_COM_ALIBABA_DRUID=INFO

cd "$(dirname "$BIN")" || exit 3
timeout 45 "$BIN" 2>&1 | grep -iE "connecting with url|Connection error|password|APPLICATION FAILED|Started EcBusinessApiApplication|Tomcat started" | head -n 20
