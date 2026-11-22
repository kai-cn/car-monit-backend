#!/usr/bin/env bash
# @description 历史脚本 slim-probe2.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash slim-probe2.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
B=/home/dev/k3s-build
for j in api backend; do
  echo "=== $j.jar platform-specific / provided-ish nested jars ==="
  unzip -l "$B/$j.jar" | awk '{print $4}' | grep -E '^BOOT-INF/lib/' | grep -E 'aarch|osx|windows|linux-x86|flink-|pulsar|grpc|zstd|bouncy|bcprov|elasticsearch|lucene|calcite|groovy|poi-ooxml-schemas|aliyun-sdk-mns|xmlbeans|snappy' | head -40
  echo "=== $j.jar total entries / lib count ==="
  unzip -l "$B/$j.jar" | grep -c 'BOOT-INF/lib/'
done
echo "=== jar full sizes in bytes ==="
stat -c '%n %s' "$B/api.jar" "$B/backend.jar"
echo "=== jlink availability ==="
/home/dev/.cache/ci-toolchain/jdk-25.0.5+8/bin/jlink --version
echo "=== jdeps modules for api (sample) ==="
/home/dev/.cache/ci-toolchain/jdk-25.0.5+8/bin/jdeps --ignore-missing-deps --print-module-deps "$B/api.jar" 2>/dev/null | head -3
