#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
J=$(find /home/dev/.m2/repository/com/alibaba -name 'druid-spring-boot-4-starter-*.jar' -o -name 'druid-spring-boot-3-starter-*.jar' 2>/dev/null | head -1)
echo "JAR=$J"
if [[ -n "$J" ]]; then
  unzip -l "$J" | grep 'DruidDataSourceWrapper'
  /home/dev/tools/mandrel-25/bin/javap -p -c -classpath "$J" com.alibaba.druid.spring.boot4.autoconfigure.DruidDataSourceWrapper 2>/dev/null | sed -n '1,140p'
fi
