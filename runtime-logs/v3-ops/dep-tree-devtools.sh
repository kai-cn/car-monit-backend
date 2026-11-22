#!/usr/bin/env bash

# @description 历史脚本 dep-tree-devtools.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash dep-tree-devtools.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

cd /home/dev/IdeaProjects/car-monit-backend-jdk25

/home/dev/.cache/ci-toolchain/apache-maven-3.9.9/bin/mvn -B -ntp -Dmaven.repo.local=/home/dev/.m2/repository \

  -pl ruoyi-admin dependency:tree -Dincludes=org.springframework.boot:spring-boot-devtools -Dverbose 2>&1 | tail -40

