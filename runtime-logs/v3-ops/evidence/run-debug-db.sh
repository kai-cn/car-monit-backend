#!/usr/bin/env bash
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
