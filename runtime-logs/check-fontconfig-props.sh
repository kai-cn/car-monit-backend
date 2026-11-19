#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== JDK fontconfig files ==="
ls /home/dev/.cache/ci-toolchain/jdk-25.0.5+8/lib/ | grep -i font || true
echo "=== default lucida mapping ==="
grep -E '^filename\.|\.ttf' /home/dev/.cache/ci-toolchain/jdk-25.0.5+8/lib/fontconfig.properties 2>/dev/null | head -15 || true
echo "=== libfontmanager deps in image ==="
docker run --rm --entrypoint sh car-monit-backend:local -c 'ldd /opt/jdk/lib/libfontmanager.so 2>&1 | grep -i "not found\|fontconfig" | head -8'
