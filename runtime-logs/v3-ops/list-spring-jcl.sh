#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: List repositories, classes, branches, or workflow files.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
J=/home/dev/.m2/repository/org/springframework/spring-core/7.0.10/spring-core-7.0.10.jar
ls -l "$J"
unzip -l "$J" | grep -E 'org/apache/commons/logging/impl|LogFactory'
