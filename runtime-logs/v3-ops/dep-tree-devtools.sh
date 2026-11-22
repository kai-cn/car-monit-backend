#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
cd /home/dev/IdeaProjects/car-monit-backend-jdk25
/home/dev/.cache/ci-toolchain/apache-maven-3.9.9/bin/mvn -B -ntp -Dmaven.repo.local=/home/dev/.m2/repository \
  -pl ruoyi-admin dependency:tree -Dincludes=org.springframework.boot:spring-boot-devtools -Dverbose 2>&1 | tail -40
