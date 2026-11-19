#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: List repositories, classes, branches, or workflow files.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
J=$(find /home/dev/.m2/repository/org/springframework/spring-core -name 'spring-core-6.2.11.jar' | head -1)
echo "JAR=$J"
unzip -l "$J" | grep 'org/springframework/util/ConcurrentReferenceHashMap' | awk '{print $4}' | sed 's#/#.#g;s#.class$##'
