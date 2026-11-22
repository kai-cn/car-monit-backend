#!/usr/bin/env bash

# @description 历史脚本 inspect-boot4-gate.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash inspect-boot4-gate.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -e

JAR=/home/dev/.m2/repository/org/springframework/boot/spring-boot/4.1.2/spring-boot-4.1.2.jar

D=/tmp/sb4inspect

rm -rf "$D"; mkdir -p "$D"; cd "$D"

unzip -q "$JAR" 'org/springframework/boot/SpringApplication*.class'

/home/dev/tools/mandrel-25/bin/javap -p -c -classpath . org.springframework.boot.SpringApplication > SpringApplication.javap.txt

echo '=== references to NativeImageRequirements ==='

grep -n -i 'NativeImageRequirements\|JavaVersion\|at least Java' SpringApplication.javap.txt | head -60 || true

echo '=== nested exception class ==='

/home/dev/tools/mandrel-25/bin/javap -p -classpath . 'org.springframework.boot.SpringApplication$NativeImageRequirementsException'

echo '=== candidate private methods ==='

grep -n 'private .*native\|private .*check\|static.*native' SpringApplication.javap.txt | head -60 || true

