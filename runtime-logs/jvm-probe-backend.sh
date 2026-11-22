#!/usr/bin/env bash

# @description 历史脚本 jvm-probe-backend.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash jvm-probe-backend.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

: "${CM_MYSQL_PWD:?} ${CM_TOKEN:?} ${CM_EXPORT_SECRET:?}"

docker rm -f jvm-probe-be >/dev/null 2>&1 || true

docker run -d --name jvm-probe-be --memory=300m --memory-swap=300m \

  --network k3d-v3 -p 19989:9989 \

  -e SPRING_DATASOURCE_DRUID_MASTER_PASSWORD="$CM_MYSQL_PWD" \

  -e TRAFFIC_API_INTERNAL_TOKEN="$CM_TOKEN" \

  -e EXPORT_DOWNLOAD_SECRET="$CM_EXPORT_SECRET" \

  -e VEHICLE_MONITOR_BASE_URL=http://172.18.0.2:30902 \

  -e SPRING_DATA_REDIS_HOST=172.18.0.1 -e SPRING_DATA_REDIS_PORT=6380 \

  --entrypoint /opt/jdk/bin/java car-monit-backend:local \

  -Xms20m -Xmx60m \

  -XX:MaxMetaspaceSize=112m -XX:CompressedClassSpaceSize=12m \

  -XX:ReservedCodeCacheSize=8m -XX:MaxDirectMemorySize=2m \

  -XX:MaxHeapFreeRatio=10 -XX:MinHeapFreeRatio=5 \

  -Xss256k -XX:CICompilerCount=2 -XX:+UseSerialGC -XX:-UsePerfData \

  -Dsun.zip.disableMemoryMapping=true \

  -Djdk.nio.maxCachedBufferSize=65536 \

  -Djava.util.concurrent.ForkJoinPool.common.parallelism=1 \

  -Dfile.encoding=UTF-8 -Duser.timezone=Asia/Shanghai \

  -jar /app/app.jar --server.port=9989 \

  --spring.datasource.driverClassName=com.mysql.cj.jdbc.Driver \

  '--spring.datasource.druid.master.url=jdbc:mysql://172.18.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8&allowMultiQueries=true' \

  --spring.main.lazy-initialization=true \

  --server.tomcat.threads.max=2 --server.tomcat.threads.min-spare=1 \

  --spring.task.scheduling.pool.size=1 \

  --spring.datasource.druid.initial-size=1 \

  --spring.datasource.druid.min-idle=1 \

  --spring.datasource.druid.max-active=2 \

  --logging.level.root=WARN --logging.level.com.baomidou=WARN >/dev/null



for i in $(seq 1 18); do

  sleep 8

  st=$(docker inspect jvm-probe-be --format '{{.State.Status}} oom={{.State.OOMKilled}}' 2>/dev/null)

  mem=$(docker stats --no-stream --format '{{.MemUsage}}' jvm-probe-be 2>/dev/null || true)

  echo "startup poll $i $st mem=$mem"

  code=$(curl -s -o /dev/null -w '%{http_code}' -m 5 http://127.0.0.1:19989/captchaImage 2>/dev/null || true)

  echo "  captcha=$code"

  if [ "$code" = "200" ]; then echo "SERVING"; break; fi

  if echo "$st" | grep -q 'oom=true\|exited'; then break; fi

done

echo "=== steady ==="

for i in 1 2 3; do sleep 8; docker stats --no-stream --format '{{.MemUsage}}' jvm-probe-be 2>/dev/null; done

echo "=== login flow ==="

CAP=$(curl -s -m 10 http://127.0.0.1:19989/captchaImage)

UUID=$(echo "$CAP" | jq -r .uuid 2>/dev/null)

ANS=$(redis-cli -h 172.18.0.1 -p 6380 GET "captcha_codes:$UUID" 2>/dev/null | tr -d '"')

echo "uuid=${UUID:0:12} answer=$ANS"

BODY=$(printf '{"username":"admin","password":"${CARMONIT_ADMIN_PASSWORD}","code":"%s","uuid":"%s"}' "$ANS" "$UUID")

curl -s -m 15 -X POST -H 'Content-Type: application/json' -d "$BODY" http://127.0.0.1:19989/login | head -c 160; echo

echo "=== markers ==="

docker logs jvm-probe-be > /tmp/jvm-probe-be.log 2>&1 || true

grep -E 'Started |Application run failed|OutOfMemoryError' /tmp/jvm-probe-be.log | head -8

echo "=== cleanup ==="

docker rm -f jvm-probe-be >/dev/null 2>&1 || true

