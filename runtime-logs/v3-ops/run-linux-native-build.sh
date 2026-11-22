#!/usr/bin/env bash
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
