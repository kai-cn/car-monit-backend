#!/usr/bin/env bash

# @description 历史脚本 jvm-probe5.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash jvm-probe5.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

: "${CM_OGAUSS_PWD:?} ${CM_TOKEN:?}"

docker rm -f jvm-probe >/dev/null 2>&1 || true

docker run -d --name jvm-probe --memory=300m --memory-swap=300m \

  --network k3d-v3 -p 19902:9902 \

  -e SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$CM_OGAUSS_PWD" \

  -e TRAFFIC_INTERNAL_TOKEN="$CM_TOKEN" \

  -e SPRING_DATA_REDIS_HOST=172.18.0.1 -e SPRING_DATA_REDIS_PORT=6380 \

  --entrypoint /opt/jdk/bin/java car-monit-api:local \

  --add-opens=java.base/java.lang=ALL-UNNAMED \

  -Xms24m -Xmx56m \

  -XX:MaxMetaspaceSize=116m -XX:CompressedClassSpaceSize=12m \

  -XX:ReservedCodeCacheSize=6m -XX:MaxDirectMemorySize=4m \

  -XX:MaxHeapFreeRatio=10 -XX:MinHeapFreeRatio=5 \

  -Xss256k -XX:CICompilerCount=2 -XX:+UseSerialGC \

  -Dsun.zip.disableMemoryMapping=true \

  -Djava.util.concurrent.ForkJoinPool.common.parallelism=1 \

  -Dfile.encoding=UTF-8 -Duser.timezone=Asia/Shanghai \

  -jar /app/app.jar --server.port=9902 \

  '--spring.datasource.dynamic.datasource.master.url=jdbc:postgresql://172.18.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&tinyInt1isBit=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai' \

  --traffic.query.engine=legacy --traffic.sync.enabled=false \

  --server.tomcat.threads.max=2 --server.tomcat.threads.min-spare=1 \

  --spring.task.scheduling.pool.size=1 \

  --spring.datasource.dynamic.druid.initial-size=1 \

  --spring.datasource.dynamic.druid.min-idle=1 \

  --spring.datasource.dynamic.druid.max-active=2 \

  --logging.level.p6spy=OFF --logging.level.com.baomidou=WARN >/dev/null



for i in $(seq 1 24); do

  sleep 8

  st=$(docker inspect jvm-probe --format '{{.State.Status}} oom={{.State.OOMKilled}}' 2>/dev/null)

  mem=$(docker stats --no-stream --format '{{.MemUsage}}' jvm-probe 2>/dev/null || true)

  echo "poll $i $st mem=$mem"

  if docker logs jvm-probe 2>&1 | grep -q 'Started .* in .* seconds'; then echo "STARTED"; break; fi

  if echo "$st" | grep -q 'oom=true'; then echo "OOMKILLED"; break; fi

  if echo "$st" | grep -q 'exited'; then echo "EXITED"; break; fi

done

docker logs jvm-probe > /tmp/jvm-probe7.log 2>&1 || true

echo "=== markers ==="

grep -E 'Started |APPLICATION FAILED|Application run failed|OutOfMemoryError|Exception encountered' /tmp/jvm-probe7.log | head -12

echo "=== readiness ==="

curl -s -o /dev/null -w 'no-token http=%{http_code}\n' -m 10 http://127.0.0.1:19902/api/v3/es/readiness

curl -s -o /dev/null -w 'with-token http=%{http_code}\n' -m 10 -H 'X-Internal-Token: local-dev-internal-token-0123456789' http://127.0.0.1:19902/api/v3/es/readiness

curl -s -o /dev/null -w 'section http=%{http_code}\n' -m 20 -H 'X-Internal-Token: local-dev-internal-token-0123456789' 'http://127.0.0.1:19902/base/section/list?pageNum=1&pageSize=5'

echo "=== cleanup ==="

docker rm -f jvm-probe >/dev/null 2>&1 || true

