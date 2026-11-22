#!/usr/bin/env bash

# @description 历史脚本 step19-cluster-login.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash step19-cluster-login.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

BE=http://172.18.0.2:30989

API=http://172.18.0.2:30902

H="X-Internal-Token: local-dev-internal-token-0123456789"

echo "=== cluster full login (real captcha, 400Mi pod) ==="

CAP=$(curl -s -m 20 "$BE/captchaImage")

UUID=$(echo "$CAP" | jq -r .uuid 2>/dev/null)

echo "captcha has_img=$(echo "$CAP" | jq -r '.img != null' 2>/dev/null) uuid=${UUID:0:16}"

ANS=$(redis-cli -h 127.0.0.1 -p 6380 GET "captcha_codes:$UUID" 2>/dev/null | tr -d '"' | grep -oE '[0-9+-]+' | head -1)

BODY=$(printf '{"username":"admin","password":"${CARMONIT_ADMIN_PASSWORD}","code":"%s","uuid":"%s"}' "$ANS" "$UUID")

LOGIN=$(curl -s -m 25 -X POST -H 'Content-Type: application/json' -d "$BODY" "$BE/login")

echo "login=$(echo "$LOGIN" | head -c 130)"

TOK=$(echo "$LOGIN" | jq -r .token 2>/dev/null)

if [ -n "$TOK" ] && [ "$TOK" != "null" ]; then

  echo "=== authenticated endpoints ==="

  for u in /getInfo /getRouters '/system/user/list?pageNum=1&pageSize=5' '/manager/carinfo/list?pageNum=1&pageSize=5' /monitor/server '/manager/carinfo/export'; do

    printf '  %-50s ' "$u"

    curl -s -o /dev/null -w 'http=%{http_code}\n' -m 30 -H "Authorization: Bearer $TOK" "$BE$u"

  done

  echo "=== cross-service export submit (ClusterDNS) ==="

  curl -s -m 30 -X POST -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \

    -d '{"type":"snapshot","startTime":"2025-11-01 00:00:00","endTime":"2025-11-30 23:59:59"}' \

    "$BE/manager/bigScreen/export/display" | head -c 180; echo

fi

echo "=== api endpoints ==="

curl -s -o /dev/null -w '  no-token=%{http_code}\n' -m 15 "$API/api/v3/es/readiness"

curl -s -o /dev/null -w '  readiness=%{http_code}\n' -m 15 -H "$H" "$API/api/v3/es/readiness"

curl -s -m 20 -H "$H" "$API/base/gantry/list?pageNum=1&pageSize=3" | head -c 90; echo

echo "=== ERROR-only log verification (count non-ERROR lines) ==="

for app in car-monit-api car-monit-backend; do

  logs=$(docker exec k3d-v3-server-0 kubectl logs deploy/"$app" --tail=200 2>/dev/null)

  total=$(echo "$logs" | wc -l)

  errs=$(echo "$logs" | grep -c 'ERROR' || true)

  infos=$(echo "$logs" | grep -cE 'INFO|DEBUG|TRACE| Consume Time| Execute SQL' || true)

  echo "$app: lines=$total error_lines=$errs non_error_log_lines=$infos"

  echo "$logs" | tail -3

done

