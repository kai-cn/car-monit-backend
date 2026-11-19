#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Extract structured matches (paths/options) from long command lines or logs.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 /mnt/d/work/runtime-logs/v3-ops/grep-classpath.py \
  /mnt/d/work/runtime-logs/v3-ops/evidence/native-backend-jdk25-ext4-linuxmvn-r4.log \
  'spring-boot-devtools[^:]*\.jar' | sort -u
