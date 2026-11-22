#!/usr/bin/env bash
# @description 历史脚本 probe-druid-builder.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash probe-druid-builder.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
J=/home/dev/.m2/repository/com/alibaba/druid-spring-boot-4-starter/1.2.28/druid-spring-boot-4-starter-1.2.28.jar
/home/dev/tools/mandrel-25/bin/javap -p -c -classpath "$J" com.alibaba.druid.spring.boot4.autoconfigure.DruidDataSourceBuilder | sed -n '1,140p'
