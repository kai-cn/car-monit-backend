#!/usr/bin/env bash

# @description 历史脚本 step15-db-limits.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash step15-db-limits.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

BE=http://127.0.0.1:19989

API=http://127.0.0.1:19902

TOKENH='X-Internal-Token: local-dev-internal-token-0123456789'



echo "=== 1) full login flow with real captcha (-Xmx96m / 400m) ==="

CAP=$(curl -s -m 20 "$BE/captchaImage")

UUID=$(echo "$CAP" | jq -r .uuid 2>/dev/null)

echo "captcha uuid=${UUID:0:16} has_img=$(echo "$CAP" | jq -r '.img != null' 2>/dev/null)"

ANS=$(redis-cli -h 127.0.0.1 -p 6380 GET "captcha_codes:$UUID" 2>/dev/null | tr -d '"' | grep -oE '[0-9+-]+' | head -1)

echo "captcha answer=$ANS"

BODY=$(printf '{"username":"admin","password":"Admin@2025-","code":"%s","uuid":"%s"}' "$ANS" "$UUID")

LOGIN=$(curl -s -m 25 -X POST -H 'Content-Type: application/json' -d "$BODY" "$BE/login")

echo "login=$(echo "$LOGIN" | head -c 150)"

TOK=$(echo "$LOGIN" | jq -r .token 2>/dev/null)

echo "token_len=${#TOK}"

if [ -n "$TOK" ] && [ "$TOK" != "null" ]; then

  for u in /getInfo /getRouters '/system/user/list?pageNum=1&pageSize=5' '/manager/carinfo/list?pageNum=1&pageSize=5' /monitor/server '/manager/carinfo/export'; do

    printf '  %-50s ' "$u"

    curl -s -o /dev/null -w 'http=%{http_code}\n' -m 30 -H "Authorization: Bearer $TOK" "$BE$u"

  done

  echo "  === cross-service export submit ==="

  curl -s -m 30 -X POST -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \

    -d '{"type":"snapshot","startTime":"2025-11-01 00:00:00","endTime":"2025-11-30 23:59:59"}' \

    "$BE/manager/bigScreen/export/display" | head -c 180; echo

fi



echo "=== 2) DB memory peak during real query load (30 samples @1s) ==="

MAX_MY=0; MAX_OG=0

for i in $(seq 1 30); do

  curl -s -o /dev/null -m 8 -H "$TOKENH" "$API/base/gantry/list?pageNum=1&pageSize=10" 2>/dev/null

  curl -s -o /dev/null -m 8 -H "$TOKENH" "$API/base/section/list?pageNum=1&pageSize=10" 2>/dev/null

  if [ -n "${TOK:-}" ] && [ "$TOK" != "null" ]; then

    curl -s -o /dev/null -m 8 -H "Authorization: Bearer $TOK" "$BE/system/user/list?pageNum=1&pageSize=10" 2>/dev/null

  fi

  line=$(docker stats --no-stream --format '{{.Name}} {{.MemUsage}}' mysql_wsl opengauss 2>/dev/null)

  my=$(echo "$line" | awk '/mysql_wsl/{gsub(/MiB/,"",$2); print $2}')

  og=$(echo "$line" | awk '/opengauss/{gsub(/MiB/,"",$2); print $2}')

  MAX_MY=$(awk -v a="$MAX_MY" -v b="${my:-0}" 'BEGIN{print (b>a?b:a)}')

  MAX_OG=$(awk -v a="$MAX_OG" -v b="${og:-0}" 'BEGIN{print (b>a?b:a)}')

  sleep 1

done

echo "PEAK mysql_wsl=${MAX_MY}MiB opengauss=${MAX_OG}MiB"



echo "=== 3) apply 500m hard limits and verify ==="

docker update --memory=500m --memory-swap=500m mysql_wsl >/dev/null

docker update --memory=500m --memory-swap=500m opengauss >/dev/null

for c in mysql_wsl opengauss; do docker inspect --format '{{.Name}} mem={{.HostConfig.Memory}} swap={{.HostConfig.MemorySwap}} oom={{.State.OOMKilled}}' "$c"; done

sleep 5

for u in '/base/gantry/list?pageNum=1&pageSize=5'; do

  printf '  api@500m %-40s ' "$u"

  curl -s -o /dev/null -w 'http=%{http_code}\n' -m 20 -H "$TOKENH" "$API$u"

done



echo "=== 4) tighten to measured minimal (<=500m) and verify ==="

MY_LIMIT=$(( ${MAX_MY%.*} + 96 )); [ "$MY_LIMIT" -gt 500 ] && MY_LIMIT=500

OG_LIMIT=$(( ${MAX_OG%.*} + 96 )); [ "$OG_LIMIT" -gt 500 ] && OG_LIMIT=500

[ "$MY_LIMIT" -lt 256 ] && MY_LIMIT=256

[ "$OG_LIMIT" -lt 256 ] && OG_LIMIT=256

echo "chosen limits: mysql=${MY_LIMIT}m opengauss=${OG_LIMIT}m (peak + 96MiB headroom, hard cap 500m)"

docker update --memory="${MY_LIMIT}m" --memory-swap="${MY_LIMIT}m" mysql_wsl >/dev/null

docker update --memory="${OG_LIMIT}m" --memory-swap="${OG_LIMIT}m" opengauss >/dev/null

for c in mysql_wsl opengauss; do docker inspect --format '{{.Name}} mem={{.HostConfig.Memory}} oom={{.State.OOMKilled}} status={{.State.Status}}' "$c"; done

sleep 5

echo "  === post-limit regression ==="

curl -s -o /dev/null -w '  api gantry http=%{http_code}\n' -m 20 -H "$TOKENH" "$API/base/gantry/list?pageNum=1&pageSize=5"

curl -s -o /dev/null -w '  api section http=%{http_code}\n' -m 20 -H "$TOKENH" "$API/base/section/list?pageNum=1&pageSize=5"

if [ -n "${TOK:-}" ] && [ "$TOK" != "null" ]; then

  curl -s -o /dev/null -w '  backend user list http=%{http_code}\n' -m 20 -H "Authorization: Bearer $TOK" "$BE/system/user/list?pageNum=1&pageSize=5"

fi

docker stats --no-stream --format '{{.Name}} {{.MemUsage}}' mysql_wsl opengauss

