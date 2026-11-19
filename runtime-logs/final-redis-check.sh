#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== verify-login (reads captcha code from redis-single:6379) ==="
bash /mnt/d/work/runtime-logs/verify-login.sh
echo "=== redis-single clients AFTER captcha (expect >1) ==="
redis-cli -p 6379 info clients 2>/dev/null | grep connected_clients
echo "=== captcha keys in 6379 (expect >=1) ==="
redis-cli -p 6379 --scan --pattern 'captcha_codes:*' 2>/dev/null | wc -l
