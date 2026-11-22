#!/usr/bin/env bash

# @description 历史脚本 run-linux-native-build.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash run-linux-native-build.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Run a build/verification command with a fixed environment and write evidence.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Wrapper: build the api-jdk25 Spring Boot 4 native ELF inside WSL2.

set -euo pipefail

export MANDREL_HOME=/home/dev/tools/mandrel-25

export MVN=/mnt/d/work/apache-maven/bin/mvn

export MAVEN_REPO=/home/dev/.m2/repository

export WORK_ROOT=/home/dev/native-work

export EVIDENCE_DIR=/mnt/d/work/runtime-logs/v3-ops/evidence

exec bash /mnt/d/work/IdeaProjects/car-monit-api-java-V3/scripts/v3/ops/v3-native-build-linux.sh \

  api 25 /mnt/d/work/IdeaProjects/car-monit-api-jdk25 api-jdk25-linux

