#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== backend log: netty/unsafe/direct memory ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=300 2>&1 | grep -E 'ByteBufAllocator|ExceptionInInitializerError|Unsafe|direct buffer|Direct buffer|OutOfMemoryError|NoClassDefFoundError|Fontconfig|Caused by' | head -20
echo "=== api log: same ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-api --tail=200 2>&1 | grep -E 'ByteBufAllocator|ExceptionInInitializerError|Unsafe|Direct buffer|OutOfMemoryError|NoClassDefFoundError|Caused by' | head -12
