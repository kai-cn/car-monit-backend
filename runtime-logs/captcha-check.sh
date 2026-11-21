#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
for i in 1 2 3 4 5; do
  echo -n "captcha try $i: HTTP="
  curl -s -m 10 -o /dev/null -w '%{http_code}' http://172.18.0.5:30989/captchaImage
  echo
done
