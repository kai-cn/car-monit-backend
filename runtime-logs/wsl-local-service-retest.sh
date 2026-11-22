#!/usr/bin/env bash
# @description 历史脚本 wsl-local-service-retest.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash wsl-local-service-retest.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程；Java 运行时
# Purpose: run locally packaged backend Boot2 jar against WSL Docker databases.
# Idea:
# - start Redis container if absent; MySQL is already on 3307.
# - run freshly packaged backend master jar with local MySQL/Redis DSNs.
# - generate JUnit suites from full backend endpoint list and run contract/load suites.
# Risk: starts a local process on 127.0.0.1:19903 and writes evidence under runtime-logs.
set -uo pipefail
ROOT=/mnt/d/work/runtime-logs
OUT=$ROOT/wsl-service-retest
JUNIT=$ROOT/junit-platform-console-standalone.jar
JAR=$(python3 -c "import json; d=json.load(open('$ROOT/local-package-evidence/local-package-results.json',encoding='utf-8')); print(next(x['jar'] for x in d if x['app']=='backend' and x['branch']=='master'))" 2>/dev/null || true)
EP=$(python3 -c "print('$ROOT/api-endpoints-full.txt')")
mkdir -p "$OUT/logs" /home/ruoyi/logs 2>/dev/null || true

if [ -z "$JAR" ] || [ ! -f "$JAR" ]; then
  echo "NO_LOCAL_JAR $JAR" >&2
  exit 2
fi
if ! docker ps --format '{{.Names}}' | grep -q '^redis_wsl$'; then
  docker run -d --name redis_wsl -p 6379:6379 redis:7-alpine >/dev/null
fi
for i in $(seq 1 30); do docker exec redis_wsl redis-cli ping >/dev/null 2>&1 && break; sleep 1; done

export BASE_URL=http://127.0.0.1:19903
export OUT_DIR=$OUT
export LOG_PATH=$OUT/logs
export HTTP_TIMEOUT_MS=60000
java -jar "$JAR" \
  --server.port=19903 \
  --spring.main.allow-circular-references=true \
  --spring.main.lazy-initialization=true \
  --spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration \
  --spring.datasource.druid.master.url='jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8' \
  --spring.datasource.druid.master.username=root \
  --spring.datasource.druid.master.password=root \
  --spring.redis.host=127.0.0.1 --spring.redis.port=6379 \
  --token.secret=junit-cloud-secret-deterministic-0123456789abcdef \
  > "$OUT/app.log" 2>&1 &
echo $! > "$OUT/app.pid"
for i in $(seq 1 180); do
  if (echo > /dev/tcp/127.0.0.1/19903) >/dev/null 2>&1; then echo "SERVICE_READY after ${i}s"; break; fi
  if ! kill -0 "$(cat "$OUT/app.pid")" 2>/dev/null; then echo "SERVICE_EXITED"; tail -80 "$OUT/app.log"; exit 1; fi
  sleep 1
done

python3 "$ROOT/generate_junit_suite.py" --endpoints "$EP" --out "$OUT/generated"
mkdir -p "$OUT/classes"
javac -encoding UTF-8 -source 8 -target 8 -cp "$JUNIT" -d "$OUT/classes" "$OUT"/generated/*.java
java -jar "$JUNIT" execute --class-path "$OUT/classes" \
  --select-class com.ruoyi.parity.generated.EndpointContractTest \
  --details=summary --reports-dir "$OUT/contract-reports" 2>&1 | tee "$OUT/contract.log"
LOAD_THREADS=4 LOAD_SECONDS=15 LOAD_WARMUP_SECONDS=1 \
java -jar "$JUNIT" execute --class-path "$OUT/classes" \
  --select-class com.ruoyi.parity.generated.EndpointLoadTest \
  --details=summary --reports-dir "$OUT/load-reports" 2>&1 | tee "$OUT/load.log"

if [ -f "$OUT/app.pid" ]; then kill "$(cat "$OUT/app.pid")" 2>/dev/null || true; fi
echo "LOCAL_SERVICE_RETEST_DONE"
