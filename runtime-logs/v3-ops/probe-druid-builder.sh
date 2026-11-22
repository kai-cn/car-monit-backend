#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
J=/home/dev/.m2/repository/com/alibaba/druid-spring-boot-4-starter/1.2.28/druid-spring-boot-4-starter-1.2.28.jar
/home/dev/tools/mandrel-25/bin/javap -p -c -classpath "$J" com.alibaba.druid.spring.boot4.autoconfigure.DruidDataSourceBuilder | sed -n '1,140p'
