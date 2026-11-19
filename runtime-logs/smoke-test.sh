#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# k3d 冒烟测试（CI java-smoke 作业内容）
# 从 WSL 主机经 NodePort 校验 backend/api 关键端点
NODE=172.18.0.5
BE_PORT=30989
API_PORT=30902
fail=0
chk() { if [ "$2" = "$3" ]; then echo "PASS $1 = $3"; else echo "FAIL $1 (expect $2 got $3)"; fail=1; fi; }

c=$(curl -s -m 10 -o /dev/null -w '%{http_code}' "http://$NODE:$BE_PORT/captchaImage"); chk backend-captcha 200 "$c"
c=$(curl -s -m 8  -o /dev/null -w '%{http_code}' "http://$NODE:$API_PORT/api/v3/es/readiness"); chk api-guard-no-token 403 "$c"
c=$(curl -s -m 8  -o /dev/null -w '%{http_code}' "http://$NODE:$API_PORT/base/section/list"); chk api-section-list 200 "$c"
c=$(curl -s -m 8  -o /dev/null -w '%{http_code}' "http://$NODE:$API_PORT/base/gantry/list"); chk api-gantry-list 200 "$c"

if [ $fail -eq 0 ]; then echo "SMOKE_ALL_PASS"; else echo "SMOKE_HAS_FAILURE"; fi
exit $fail
