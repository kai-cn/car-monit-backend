#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Run a build/verification command with a fixed environment and write evidence.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
cd /home/dev/IdeaProjects/car-monit-backend-jdk25/ruoyi-admin/target
export EXPORT_DOWNLOAD_SECRET=local-verify-backend25-secret-key
timeout 90 ./ruoyi-admin \
  --server.port=19903 \
  -Dorg.apache.commons.logging.LogFactory=org.apache.commons.logging.impl.Slf4jLogFactory \
  '--spring.datasource.druid.master.url=jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=GMT%2B8&allowMultiQueries=true' \
  --spring.datasource.druid.master.username=root \
  --spring.datasource.druid.master.password=root \
  --spring.datasource.druid.master.driverClassName=com.mysql.cj.jdbc.Driver \
  > /tmp/backend25-native16.log 2>&1
echo RC=$?
