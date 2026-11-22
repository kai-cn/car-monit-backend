#!/usr/bin/env bash

# @description 历史脚本 syntax-check.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash syntax-check.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

OPS=/mnt/d/work/IdeaProjects/car-monit-api-java-V3/scripts/v3/ops

for s in v3-run-native-linux.sh v3-run-jvm-linux.sh v3-probe-http.sh v3-compare-native-jvm.sh v3-verify-jdk-matrix.sh; do

  if bash -n "$OPS/$s" 2>/tmp/bashn.err; then echo "OK $s"; else echo "FAIL $s"; cat /tmp/bashn.err; fi

done

for s in build-jvm-jar.sh probe-db-env.sh probe-toolchain.sh probe-build-status.sh probe-all-java.sh; do

  if bash -n "/mnt/d/work/runtime-logs/v3-ops/$s" 2>/tmp/bashn.err; then echo "OK $s"; else echo "FAIL $s"; cat /tmp/bashn.err; fi

done

