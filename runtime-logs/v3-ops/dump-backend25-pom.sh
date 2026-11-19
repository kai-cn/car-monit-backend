#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Print a file section for diagnosis.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
grep -n -A 12 'native-maven-plugin' /home/dev/IdeaProjects/car-monit-backend-jdk25/ruoyi-admin/pom.xml | head -30
