#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== WSL fonts ==="
find /usr/share/fonts /usr/local/share/fonts -type f \( -iname '*.ttf' -o -iname '*.ttc' \) 2>/dev/null | head -10
echo "=== Windows fonts (mounted) ==="
find /mnt/d/../c/Windows/Fonts /mnt/c/Windows/Fonts -maxdepth 1 -type f -iname '*.ttf' 2>/dev/null | head -10
echo "=== fontconfig in base image ==="
docker run --rm --entrypoint sh mysql:8.0.30 -c 'command -v fc-cache || echo "no fc-cache"; ls -la /usr/share/fonts 2>/dev/null | head -8; ldconfig -p 2>/dev/null | grep -i fontconfig | head -3'
