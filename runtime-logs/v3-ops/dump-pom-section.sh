#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Print a file section for diagnosis.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
sed -n '148,190p' /home/dev/IdeaProjects/car-monit-api-jdk21/pro-business-api/pom.xml
