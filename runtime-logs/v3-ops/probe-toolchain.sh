#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo '=== WSL JDKs ==='
ls -d /home/dev/.cache/ci-toolchain/jdk-* 2>/dev/null
echo '=== Mandrels ==='
ls -d /home/dev/tools/mandrel-* 2>/dev/null
echo '=== Maven ==='
which mvn 2>/dev/null || true
/home/dev/.cache/ci-toolchain/apache-maven-3.9.9/bin/mvn -v 2>/dev/null | head -3 || true
echo '=== r15 native gate evidence ==='
grep -E 'NativeImageRequirementsException|must support at least Java 25' /mnt/d/work/runtime-logs/v3-ops/evidence/native-run-linux-api-jdk21-linux-r15.log 2>/dev/null | head -5
