#!/usr/bin/env bash

# @description 历史脚本 dep-tree-backend.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash dep-tree-backend.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

cd /mnt/d/work/IdeaProjects/car-monit-backend-jdk21

/mnt/d/work/apache-maven/bin/mvn -B -ntp -Dmaven.repo.local=/home/dev/.m2/repository \

  -pl ruoyi-admin dependency:tree -Dincludes=org.apache.logging.log4j:*,log4j:log4j,org.slf4j:* \

  -Dverbose 2>&1 | grep -E '^\[INFO\] [+\\|]|log4j|slf4j' | head -120

