#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -e
JAR=/home/dev/.m2/repository/org/springframework/boot/spring-boot/4.1.2/spring-boot-4.1.2.jar
D=/tmp/sb4inspect
rm -rf "$D"; mkdir -p "$D"; cd "$D"
unzip -q "$JAR" 'org/springframework/boot/SpringApplication*.class'
/home/dev/tools/mandrel-25/bin/javap -p -c -classpath . org.springframework.boot.SpringApplication > SpringApplication.javap.txt
echo '=== references to NativeImageRequirements ==='
grep -n -i 'NativeImageRequirements\|JavaVersion\|at least Java' SpringApplication.javap.txt | head -60 || true
echo '=== nested exception class ==='
/home/dev/tools/mandrel-25/bin/javap -p -classpath . 'org.springframework.boot.SpringApplication$NativeImageRequirementsException'
echo '=== candidate private methods ==='
grep -n 'private .*native\|private .*check\|static.*native' SpringApplication.javap.txt | head -60 || true
