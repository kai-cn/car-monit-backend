#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
B=/home/dev/k3s-build
echo "=== flink libs in api.jar ==="
unzip -l "$B/api.jar" | awk '/BOOT-INF\/lib\/flink/ {print $1, $4}'
echo "=== flink libs in backend.jar ==="
unzip -l "$B/backend.jar" | awk '/BOOT-INF\/lib\/flink/ {print $1, $4}'
echo "=== platform-specific jars in both ==="
for j in api backend; do
  echo "--- $j ---"
  unzip -l "$B/$j.jar" | awk '{print $4}' | grep -E '^BOOT-INF/lib/.*(aarch_64|osx|windows)' || true
done
