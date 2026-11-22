#!/usr/bin/env bash
# @description 历史脚本 compare-build-env.sh：对比基线/候选结果并产出报告；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash compare-build-env.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Compare two artifacts/branches/logs and emit a structured verdict.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
for f in /mnt/d/work/runtime-logs/v3-ops/evidence/native-api-boot4-jdk21-mandrel25-r2.log /mnt/d/work/runtime-logs/v3-ops/evidence/native-api-jdk21-ext4-linuxmvn-r2.log; do
  echo "=== $f ==="
  grep -c 'graalvm reachability metadata repository for' "$f"
  grep -m1 'Downloaded GraalVM reachability' "$f"
  grep -m1 'native-maven-plugin' "$f"
done
