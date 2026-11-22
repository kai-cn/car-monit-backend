#!/usr/bin/env bash
# @description 历史脚本 wsl-local-service-retest3.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash wsl-local-service-retest3.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程；Java 运行时
# Purpose: run locally packaged backend jar against WSL Docker databases.
# Idea: start Redis, launch jar with local MySQL settings, run generated JUnit contract/load suites.
# Risk: starts a local process on 127.0.0.1:19903; writes evidence only under /home/dev/local-retest.
set -uo pipefail
ROOT=/mnt/d/work/runtime-logs
OUT=/home/dev/local-retest
mkdir -p "$OUT/logs" "$OUT/contract-reports" "$OUT/load-reports" /home/ruoyi/logs 2>/dev/null || true
JUNIT=$ROOT/junit-platform-console-standalone.jar
JAR=/home/dev/local-package/backend-master/ruoyi-admin/target/ruoyi-admin.jar
EP=/mnt/d/work/IdeaProjects/car-monit-backend-new/scripts/v3/ops/parity/endpoints/backend-full.txt
if [ ! -f "$JAR" ]; then echo "NO_JAR $JAR" >&2; exit 2; fi
if [ ! -f "$JUNIT" ]; then echo "NO_JUNIT $JUNIT" >&2; exit 2; fi
if [ ! -f "$EP" ]; then echo "NO_ENDPOINTS $EP" >&2; exit 2; fi
if ! (echo > /dev/tcp/127.0.0.1/6379) >/dev/null 2>&1; then
  if docker ps --format '{{.Names}}' | grep -q '^redis_wsl$'; then
    docker start redis_wsl >/dev/null
  else
    docker run -d --name redis_wsl -p 6379:6379 redis:7-alpine >/dev/null
  fi
fi
for i in $(seq 1 30); do (echo > /dev/tcp/127.0.0.1/6379) >/dev/null 2>&1 && break; sleep 1; done
export BASE_URL=http://127.0.0.1:19903
export OUT_DIR=$OUT
export LOG_PATH=$OUT/logs
export HTTP_TIMEOUT_MS=60000
export SPRING__DATASOURCE__DRUID__MASTER__URL='jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8'
export SPRING__DATASOURCE__DRUID__MASTER__USERNAME=root
export SPRING__DATASOURCE__DRUID__MASTER__PASSWORD=root
export SPRING__DATASOURCE__DRUID__MASTER__DRIVERCLASSNAME=com.mysql.cj.jdbc.Driver
export SPRING__REDIS__HOST=127.0.0.1
export SPRING__REDIS__PORT=6379
export SPRING_DATA_REDIS_HOST=127.0.0.1
export SPRING_DATA_REDIS_PORT=6379
export TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef
java -jar "$JAR" --server.port=19903 \
  --spring.main.allow-circular-references=true \
  --spring.main.lazy-initialization=true \
  --spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration \
  > "$OUT/app.log" 2>&1 &
echo $! > "$OUT/app.pid"
READY=0
for i in $(seq 1 180); do
  if (echo > /dev/tcp/127.0.0.1/19903) >/dev/null 2>&1; then echo "SERVICE_READY after ${i}s"; READY=1; break; fi
  if ! kill -0 "$(cat "$OUT/app.pid")" 2>/dev/null; then echo SERVICE_EXITED; tail -80 "$OUT/app.log"; exit 1; fi
  sleep 1
done
if [ "$READY" -ne 1 ]; then echo SERVICE_TIMEOUT; tail -80 "$OUT/app.log"; exit 1; fi
python3 "$ROOT/generate_junit_suite.py" --endpoints "$EP" --out "$OUT/generated"
mkdir -p "$OUT/classes"
javac -encoding UTF-8 -source 8 -target 8 -cp "$JUNIT" -d "$OUT/classes" "$OUT"/generated/*.java
java -jar "$JUNIT" execute --class-path "$OUT/classes" --select-class com.ruoyi.parity.generated.EndpointContractTest --details=summary --reports-dir "$OUT/contract-reports" 2>&1 | tee "$OUT/contract.log"
LOAD_THREADS=4 LOAD_SECONDS=15 LOAD_WARMUP_SECONDS=1 java -jar "$JUNIT" execute --class-path "$OUT/classes" --select-class com.ruoyi.parity.generated.EndpointLoadTest --details=summary --reports-dir "$OUT/load-reports" 2>&1 | tee "$OUT/load.log"
if [ -f "$OUT/app.pid" ]; then kill "$(cat "$OUT/app.pid")" 2>/dev/null || true; fi
echo LOCAL_SERVICE_RETEST_DONE
