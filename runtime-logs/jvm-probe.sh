#!/usr/bin/env bash

# @description 历史脚本 jvm-probe.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash jvm-probe.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

: "${CM_OGAUSS_PWD:?} ${CM_TOKEN:?}"

LOG=/tmp/jvm-probe-api.log

rm -f "$LOG"

docker rm -f jvm-probe >/dev/null 2>&1 || true

echo "=== start api in a hard 300m cgroup ==="

docker run -d --name jvm-probe --memory=300m --memory-swap=300m \

  --network k3d-v3 -p 19902:9902 \

  -e SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$CM_OGAUSS_PWD" \

  -e TRAFFIC_INTERNAL_TOKEN="$CM_TOKEN" \

  -e SPRING_DATA_REDIS_HOST=172.18.0.1 -e SPRING_DATA_REDIS_PORT=6380 \

  --entrypoint /opt/jdk/bin/java car-monit-api:local \

  --add-opens=java.base/java.lang=ALL-UNNAMED \

  -Xms32m -Xmx88m \

  -XX:MaxMetaspaceSize=128m -XX:CompressedClassSpaceSize=24m \

  -XX:ReservedCodeCacheSize=16m -XX:MaxDirectMemorySize=16m \

  -Xss256k -XX:CICompilerCount=2 -XX:+UseSerialGC \

  -XX:+ExitOnOutOfMemoryError \

  -Dfile.encoding=UTF-8 -Duser.timezone=Asia/Shanghai \

  -jar /app/app.jar \

  --server.port=9902 \

  '--spring.datasource.dynamic.datasource.master.url=jdbc:postgresql://172.18.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&tinyInt1isBit=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai' \

  --traffic.query.engine=legacy --traffic.sync.enabled=false >/dev/null



for i in $(seq 1 18); do

  sleep 10

  st=$(docker inspect jvm-probe --format '{{.State.Status}}' 2>/dev/null || echo gone)

  mem=$(docker stats --no-stream --format '{{.MemUsage}}' jvm-probe 2>/dev/null || true)

  started=$(grep -c 'Started .* in .* seconds' "$LOG" 2>/dev/null || true)

  echo "poll $i status=$st mem=$mem started=$started"

  if [ "$st" != "running" ]; then echo "EXITED"; break; fi

  if [ "${started:-0}" -ge 1 ]; then echo "STARTED"; break; fi

  if grep -q 'OutOfMemoryError' "$LOG" 2>/dev/null; then echo "OOM"; break; fi

done

echo "=== log tail ==="

docker logs jvm-probe --tail 20 2>&1 | tail -20

echo "=== readiness if started ==="

curl -s -o /dev/null -w 'http=%{http_code}\n' -m 10 http://127.0.0.1:19902/api/v3/es/readiness 2>&1 || true

echo "=== cleanup ==="

docker rm -f jvm-probe >/dev/null 2>&1 || true

