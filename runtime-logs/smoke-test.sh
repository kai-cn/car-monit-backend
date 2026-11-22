#!/usr/bin/env bash

# @description 历史脚本 smoke-test.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash smoke-test.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
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

