#!/usr/bin/env bash

# @description 历史脚本 jdk25-probe.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash jdk25-probe.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

: "${CM_MYSQL_PWD:?} ${CM_TOKEN:?} ${CM_EXPORT_SECRET:?}"

echo "=== JDK25 compact object headers support ==="

/home/dev/.cache/ci-toolchain/jdk-25.0.5+8/bin/java -XX:+UseCompactObjectHeaders -version 2>&1 | head -3

docker rm -f jvm-probe-be >/dev/null 2>&1 || true

docker run -d --name jvm-probe-be --memory=300m --memory-swap=300m \

  --network k3d-v3 -p 19989:9989 \

  -v /home/dev/.cache/ci-toolchain/jdk-25.0.5+8:/opt/jdk25:ro \

  -e SPRING_DATASOURCE_DRUID_MASTER_PASSWORD="$CM_MYSQL_PWD" \

  -e TRAFFIC_API_INTERNAL_TOKEN="$CM_TOKEN" \

  -e EXPORT_DOWNLOAD_SECRET="$CM_EXPORT_SECRET" \

  -e VEHICLE_MONITOR_BASE_URL=http://172.18.0.2:30902 \

  -e SPRING_DATA_REDIS_HOST=172.18.0.1 -e SPRING_DATA_REDIS_PORT=6380 \

  --entrypoint /opt/jdk25/bin/java car-monit-backend:local \

  -XX:+UseCompactObjectHeaders \

  -Xms20m -Xmx64m \

  -XX:MaxMetaspaceSize=136m -XX:CompressedClassSpaceSize=24m \

  -XX:ReservedCodeCacheSize=12m -XX:MaxDirectMemorySize=2m \

  -XX:MaxHeapFreeRatio=10 -XX:MinHeapFreeRatio=5 \

  -Xss192k -XX:CICompilerCount=2 -XX:+UseSerialGC -XX:-UsePerfData \

  -Dsun.zip.disableMemoryMapping=true -Djdk.nio.maxCachedBufferSize=65536 \

  -Djava.util.concurrent.ForkJoinPool.common.parallelism=1 \

  -Dfile.encoding=UTF-8 -Duser.timezone=Asia/Shanghai \

  -jar /app/app.jar --server.port=9989 \

  --spring.datasource.driverClassName=com.mysql.cj.jdbc.Driver \

  '--spring.datasource.druid.master.url=jdbc:mysql://172.18.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8&allowMultiQueries=true' \

  --spring.main.lazy-initialization=true \

  --server.tomcat.threads.max=2 --server.tomcat.threads.min-spare=1 \

  --spring.task.scheduling.pool.size=1 \

  --spring.datasource.druid.initial-size=1 --spring.datasource.druid.min-idle=1 --spring.datasource.druid.max-active=2 \

  --logging.level.root=WARN --logging.level.com.baomidou=WARN >/dev/null

for i in $(seq 1 15); do

  sleep 10

  st=$(docker inspect jvm-probe-be --format '{{.State.Status}} oom={{.State.OOMKilled}}' 2>/dev/null)

  mem=$(docker stats --no-stream --format '{{.MemUsage}}' jvm-probe-be 2>/dev/null || true)

  code=$(curl -s -o /dev/null -w '%{http_code}' -m 8 http://127.0.0.1:19989/captchaImage 2>/dev/null || true)

  echo "poll $i $st mem=$mem captcha=$code"

  [ "$code" = "200" ] && break

  echo "$st" | grep -q 'exited' && break

done

echo "=== steady ==="

for i in 1 2 3; do sleep 8; docker stats --no-stream --format '{{.MemUsage}}' jvm-probe-be 2>/dev/null; done

echo "=== markers ==="

docker logs jvm-probe-be 2>&1 | grep -E 'Started |Application run failed|OutOfMemoryError' | tail -6

echo "=== cleanup ==="

docker rm -f jvm-probe-be >/dev/null 2>&1 || true

