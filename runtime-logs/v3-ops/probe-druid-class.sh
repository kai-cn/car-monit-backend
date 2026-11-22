#!/usr/bin/env bash

# @description 历史脚本 probe-druid-class.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash probe-druid-class.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

J=$(find /home/dev/.m2/repository/com/alibaba -name 'druid-spring-boot-4-starter-*.jar' -o -name 'druid-spring-boot-3-starter-*.jar' 2>/dev/null | head -1)

echo "JAR=$J"

if [[ -n "$J" ]]; then

  unzip -l "$J" | grep 'DruidDataSourceWrapper'

  /home/dev/tools/mandrel-25/bin/javap -p -c -classpath "$J" com.alibaba.druid.spring.boot4.autoconfigure.DruidDataSourceWrapper 2>/dev/null | sed -n '1,140p'

fi

