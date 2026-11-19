#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Run a build/verification command with a fixed environment and write evidence.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Wrapper: bench the Linux native ELF inside WSL2.
set -u
export EVIDENCE_DIR=/mnt/d/work/runtime-logs/v3-ops/evidence
BIN=/home/dev/native-work/car-monit-api-jdk25/pro-business-api/target/pro-business-api
exec bash /mnt/d/work/IdeaProjects/car-monit-api-java-V3/scripts/v3/ops/v3-native-bench-linux.sh \
  "$BIN" 19903 api-jdk25-linux 20 \
  '--spring.datasource.dynamic.datasource.master.url=jdbc:postgresql://172.18.0.1:5432/RuoYi?useSSL=false' \
  '--spring.data.redis.host=127.0.0.1'
