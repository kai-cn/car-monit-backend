#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
cd /mnt/d/work/IdeaProjects/car-monit-backend-jdk21
/mnt/d/work/apache-maven/bin/mvn -B -ntp -Dmaven.repo.local=/home/dev/.m2/repository \
  -pl ruoyi-admin dependency:tree -Dincludes=org.apache.logging.log4j:*,log4j:log4j,org.slf4j:* \
  -Dverbose 2>&1 | grep -E '^\[INFO\] [+\\|]|log4j|slf4j' | head -120
