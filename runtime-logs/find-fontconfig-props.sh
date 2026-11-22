#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== fontconfig.properties templates on WSL ==="
find /usr /home/dev/.cache/ci-toolchain /opt -iname 'fontconfig.properties*' -o -iname 'fontconfig.bfc' 2>/dev/null | head -20
echo "=== Windows JDK fonts dir ==="
ls -la /mnt/d/jdk/temurin-17/jdk-17.0.21+9/lib/fonts/ 2>/dev/null | head -12
ls /mnt/d/jdk/temurin-17/jdk-17.0.21+9/lib/fontconfig* 2>/dev/null || true
echo "=== oracle_11g fontconfig data ==="
docker create --name font-src2 --entrypoint sleep registry.cn-hangzhou.aliyuncs.com/helowin/oracle_11g:latest 3600 >/dev/null 2>&1 || true
docker cp font-src2:/etc/fonts /tmp/oracle-fonts 2>/dev/null || true
find /tmp/oracle-fonts -maxdepth 2 -type f 2>/dev/null | head -12
docker rm -f font-src2 >/dev/null 2>&1 || true
echo "=== fontconfig lib symlink targets ==="
docker run --rm --entrypoint sh registry.cn-hangzhou.aliyuncs.com/helowin/oracle_11g:latest -c 'ls -la /usr/lib64/libfontconfig.so* /usr/lib64/libfreetype.so* 2>/dev/null | head -8'
