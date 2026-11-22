#!/bin/bash
# @description 历史脚本 verify_tz_hypothesis.sh：验证配置、构建或安全不变量；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash verify_tz_hypothesis.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程；Java 运行时
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only verification of a security or build invariant.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Verify: is the vehicleweight date diff caused by native using UTC instead of Asia/Shanghai?
set -uo pipefail
NATIVE=/mnt/d/work/runtime-logs/cicd-artifacts/native-api-jdk25-115MB/api-jdk25-linux-amd64.bin
chmod +x "$NATIVE"
GS_PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -1)
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL="jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&serverTimezone=Asia/Shanghai"
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$GS_PASS"
export EXPORT_DOWNLOAD_SECRET=x

echo "=== native with TZ=Asia/Shanghai ==="
TZ=Asia/Shanghai "$NATIVE" --server.port=19902 >/tmp/n1.log 2>&1 &
P=$!
for i in $(seq 1 60); do (echo > /dev/tcp/127.0.0.1/19902) 2>/dev/null && break; sleep 1; done
curl -s "http://127.0.0.1:19902/base/vehicleweight/map" -o /tmp/n1.body
grep -o '"checkTime":"[^"]*"' /tmp/n1.body | head -3
kill $P 2>/dev/null; wait $P 2>/dev/null

echo "=== native with -Duser.timezone=Asia/Shanghai ==="
"$NATIVE" --server.port=19902 -Duser.timezone=Asia/Shanghai >/tmp/n2.log 2>&1 &
P=$!
for i in $(seq 1 60); do (echo > /dev/tcp/127.0.0.1/19902) 2>/dev/null && break; sleep 1; done
curl -s "http://127.0.0.1:19902/base/vehicleweight/map" -o /tmp/n2.body
grep -o '"checkTime":"[^"]*"' /tmp/n2.body | head -3
kill $P 2>/dev/null; wait $P 2>/dev/null

echo "=== native default (TZ unset) ==="
env -u TZ "$NATIVE" --server.port=19902 >/tmp/n3.log 2>&1 &
P=$!
for i in $(seq 1 60); do (echo > /dev/tcp/127.0.0.1/19902) 2>/dev/null && break; sleep 1; done
curl -s "http://127.0.0.1:19902/base/vehicleweight/map" -o /tmp/n3.body
grep -o '"checkTime":"[^"]*"' /tmp/n3.body | head -3
kill $P 2>/dev/null; wait $P 2>/dev/null

echo "=== reference: jar ==="
/home/dev/tools/mandrel-25/bin/java -jar /mnt/d/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api-1.0.jar --server.port=19903 >/tmp/j1.log 2>&1 &
P=$!
for i in $(seq 1 90); do (echo > /dev/tcp/127.0.0.1/19903) 2>/dev/null && break; sleep 1; done
curl -s "http://127.0.0.1:19903/base/vehicleweight/map" -o /tmp/j1.body
grep -o '"checkTime":"[^"]*"' /tmp/j1.body | head -3
kill $P 2>/dev/null; wait $P 2>/dev/null
