#!/bin/bash
# @description 历史脚本 check_saveredis.sh：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash check_saveredis.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Investigate /base/sysutil/saveRedis 500 on native: capture the real exception at request time.
set -uo pipefail
NATIVE=/mnt/d/work/runtime-logs/cicd-artifacts/native-api-jdk25-115MB/api-jdk25-linux-amd64.bin
chmod +x "$NATIVE"
GS_PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -1)
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL="jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&serverTimezone=Asia/Shanghai"
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$GS_PASS"
export EXPORT_DOWNLOAD_SECRET=x

"$NATIVE" --server.port=19902 >/tmp/sr.log 2>&1 &
P=$!
for i in $(seq 1 60); do (echo > /dev/tcp/127.0.0.1/19902) 2>/dev/null && break; sleep 1; done
echo "=== saveRedis response ==="
curl -s -w '\nHTTP=%{http_code}\n' "http://127.0.0.1:19902/base/sysutil/saveRedis"
sleep 1
echo "=== log: lines mentioning saveRedis / redis around the call ==="
grep -n -i -A12 'saveRedis\|SysUtil\|Redis' /tmp/sr.log | grep -v 'STOPPED\|STOPPING' | tail -40
kill $P 2>/dev/null; wait $P 2>/dev/null
