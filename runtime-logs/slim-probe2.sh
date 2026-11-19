#!/usr/bin/env bash
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
