#!/usr/bin/env bash

# @description 历史脚本 acceptance.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash acceptance.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

: "${CM_TOKEN:?}"

BE=http://172.18.0.2:30989

API=http://172.18.0.2:30902

H="X-Internal-Token: $CM_TOKEN"



echo "=== api internal endpoints ==="

curl -s -o /dev/null -w 'api readiness(no token)=%{http_code}\n' -m 15 "$API/api/v3/es/readiness"

curl -s -o /dev/null -w 'api readiness(token)=%{http_code}\n' -m 15 -H "$H" "$API/api/v3/es/readiness"

curl -s -m 20 -H "$H" "$API/base/section/list?pageNum=1&pageSize=5" | head -c 90; echo

curl -s -m 20 -H "$H" "$API/base/gantry/list?pageNum=1&pageSize=5" | head -c 90; echo



echo "=== backend captcha + login ==="

CAP=$(curl -s -m 15 "$BE/captchaImage")

UUID=$(echo "$CAP" | jq -r .uuid 2>/dev/null || true)

echo "uuid=${UUID:0:16}"

RAW=$(redis-cli -h 172.18.0.1 -p 6380 GET "captcha_codes:$UUID" 2>/dev/null || true)

echo "redis_raw=${RAW:0:40}"

ANS=$(echo "$RAW" | grep -oE '[0-9]+' | head -1)

echo "answer=$ANS"

BODY='{"username":"admin","password":"${CARMONIT_ADMIN_PASSWORD}","code":"","uuid":""}'

LOGIN=$(curl -s -m 20 -X POST -H 'Content-Type: application/json' -d "$BODY" "$BE/login")

echo "login=$(echo "$LOGIN" | head -c 120)"

TOK=$(echo "$LOGIN" | jq -r .token 2>/dev/null || true)

if [ -n "$TOK" ] && [ "$TOK" != "null" ]; then

  echo "token_len=${#TOK}"

  echo "=== backend authenticated endpoints ==="

  for u in /getInfo /getRouters '/system/user/list?pageNum=1&pageSize=5' '/manager/carinfo/list?pageNum=1&pageSize=5' /monitor/server; do

    printf '%-50s ' "$u"

    curl -s -o /dev/null -w 'http=%{http_code}\n' -m 25 -H "Authorization: Bearer $TOK" "$BE$u"

  done

  echo "=== cross-service backend -> api (ClusterDNS) ==="

  curl -s -m 30 -X POST -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \

    -d '{"type":"snapshot","startTime":"2025-11-01 00:00:00","endTime":"2025-11-30 23:59:59"}' \

    "$BE/manager/bigScreen/export/display" | head -c 220; echo

  curl -s -o /dev/null -w 'topTen http=%{http_code} src=' -m 30 -H "Authorization: Bearer $TOK" "$BE/manager/bigScreen/topTen"

  curl -s -D - -o /dev/null -m 30 -H "Authorization: Bearer $TOK" "$BE/manager/bigScreen/topTen" 2>/dev/null | grep -i 'X-Data-Source' || echo 'X-Data-Source: -'

else

  echo "LOGIN FAILED - skip authenticated checks"

fi

