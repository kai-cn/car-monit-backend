#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: List repositories, classes, branches, or workflow files.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
unzip -l /home/dev/.m2/repository/commons-logging/commons-logging/1.3.6/commons-logging-1.3.6.jar | grep 'impl/'
