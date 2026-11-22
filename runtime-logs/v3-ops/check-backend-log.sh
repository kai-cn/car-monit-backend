#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
F=${1:-/tmp/backend25-native8.log}
grep -E 'Started RuoYiApplication|Tomcat started|APPLICATION FAILED|Exception in thread|port\(s\)' "$F" | head -12
echo '---TAIL---'
tail -n 18 "$F"
