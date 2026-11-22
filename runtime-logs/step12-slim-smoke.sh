#!/usr/bin/env bash

# @description 历史脚本 step12-slim-smoke.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash step12-slim-smoke.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

: "${CM_OGAUSS_PWD:?} ${CM_MYSQL_PWD:?} ${CM_TOKEN:?} ${CM_EXPORT_SECRET:?}"

echo "=== ensure shared test redis :6380 ==="

redis-cli -h 127.0.0.1 -p 6380 ping >/dev/null 2>&1 || redis-server --bind 0.0.0.0 --port 6380 --protected-mode no --save "" --appendonly no --maxmemory 64mb --daemonize yes

redis-cli -h 127.0.0.1 -p 6380 ping

echo "=== jlink runtime sanity ==="

docker run --rm --entrypoint /opt/jre/bin/java car-monit-api:slim -version 2>&1 | head -3

echo "=== fontconfig.properties check ==="

docker run --rm --entrypoint sh car-monit-api:slim -c 'ls -la /opt/jre/lib/fonts/ 2>/dev/null; ls /opt/jre/lib/fontconfig.properties 2>/dev/null || echo NO_FONTCONFIG_PROPS'



JFLAGS=(

  -XX:+UseCompactObjectHeaders

  -Xms32m -Xmx96m

  -XX:MaxMetaspaceSize=144m -XX:CompressedClassSpaceSize=24m

  -XX:ReservedCodeCacheSize=32m -XX:MaxDirectMemorySize=16m

  -XX:MaxHeapFreeRatio=10 -XX:MinHeapFreeRatio=5 -Xss512k

  -XX:CICompilerCount=2 -XX:+UseSerialGC -XX:-UsePerfData

  -Dsun.zip.disableMemoryMapping=true -Djdk.nio.maxCachedBufferSize=65536

  -Djava.util.concurrent.ForkJoinPool.common.parallelism=1

  -Dfile.encoding=UTF-8 -Duser.timezone=Asia/Shanghai

)



docker rm -f slim-api slim-be >/dev/null 2>&1 || true

echo "=== start slim api (400m) ==="

docker run -d --name slim-api --memory=400m --memory-swap=400m --network k3d-v3 -p 19902:9902 \

  -e SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$CM_OGAUSS_PWD" \

  -e TRAFFIC_INTERNAL_TOKEN="$CM_TOKEN" \

  -e SPRING_DATA_REDIS_HOST=172.18.0.1 -e SPRING_DATA_REDIS_PORT=6380 \

  --entrypoint /opt/jre/bin/java car-monit-api:slim \

  --add-opens=java.base/java.lang=ALL-UNNAMED "${JFLAGS[@]}" \

  -jar /app/app.jar --server.port=9902 \

  '--spring.datasource.dynamic.datasource.master.url=jdbc:postgresql://172.18.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&tinyInt1isBit=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai' \

  --traffic.query.engine=legacy --traffic.sync.enabled=false \

  --spring.main.lazy-initialization=true \

  --server.tomcat.max-connections=200 --server.tomcat.threads.max=8 \

  --spring.datasource.dynamic.druid.initial-size=1 --spring.datasource.dynamic.druid.min-idle=1 --spring.datasource.dynamic.druid.max-active=2 \

  --logging.level.root=ERROR >/dev/null



echo "=== start slim backend (400m) ==="

docker run -d --name slim-be --memory=400m --memory-swap=400m --network k3d-v3 -p 19989:9989 \

  -e SPRING_DATASOURCE_DRUID_MASTER_PASSWORD="$CM_MYSQL_PWD" \

  -e TRAFFIC_API_INTERNAL_TOKEN="$CM_TOKEN" -e EXPORT_DOWNLOAD_SECRET="$CM_EXPORT_SECRET" \

  -e VEHICLE_MONITOR_BASE_URL=http://172.18.0.1:19902 \

  -e SPRING_DATA_REDIS_HOST=172.18.0.1 -e SPRING_DATA_REDIS_PORT=6380 \

  --entrypoint /opt/jre/bin/java car-monit-backend:slim \

  "${JFLAGS[@]}" \

  -jar /app/app.jar --server.port=9989 \

  --spring.datasource.driverClassName=com.mysql.cj.jdbc.Driver \

  '--spring.datasource.druid.master.url=jdbc:mysql://172.18.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8&allowMultiQueries=true' \

  --spring.main.lazy-initialization=true \

  --server.tomcat.max-connections=200 --server.tomcat.threads.max=8 \

  --spring.datasource.druid.initial-size=1 --spring.datasource.druid.min-idle=1 --spring.datasource.druid.max-active=2 \

  --logging.level.root=ERROR >/dev/null



echo "=== wait for ports (max 180s) ==="

for i in $(seq 1 18); do

  sleep 10

  a=$(curl -s -o /dev/null -w '%{http_code}' -m 5 -H "X-Internal-Token: $CM_TOKEN" http://127.0.0.1:19902/api/v3/es/readiness 2>/dev/null || true)

  b=$(curl -s -o /dev/null -w '%{http_code}' -m 5 http://127.0.0.1:19989/captchaImage 2>/dev/null || true)

  ma=$(docker stats --no-stream --format '{{.MemUsage}}' slim-api 2>/dev/null || true)

  mb=$(docker stats --no-stream --format '{{.MemUsage}}' slim-be 2>/dev/null || true)

  echo "poll $i api=$a backend=$b api_mem=$ma be_mem=$mb"

  [ "$a" = "200" ] && [ "$b" = "200" ] && break

done

echo "=== endpoints ==="

curl -s -m 15 -H "X-Internal-Token: $CM_TOKEN" 'http://127.0.0.1:19902/base/section/list?pageNum=1&pageSize=3' | head -c 100; echo

curl -s -m 15 http://127.0.0.1:19989/captchaImage | head -c 140; echo

echo "=== container status ==="

docker inspect --format '{{.Name}} status={{.State.Status}} oom={{.State.OOMKilled}}' slim-api slim-be

echo "=== markers (ERROR level should be quiet) ==="

docker logs slim-api 2>&1 | tail -6

