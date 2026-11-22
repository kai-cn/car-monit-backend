#!/usr/bin/env bash
# @description 用管理员登录态重跑 WSL 本机 backend 全接口契约与压测，验证返回不再全是认证失败。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage CARMONIT_ADMIN_USER=admin CARMONIT_ADMIN_PASSWORD=... bash runtime-logs/wsl-local-auth-retest.sh
# @dependencies WSL Docker/MySQL/Redis、本地打包 jar、Python 3、JDK8、JUnit standalone。
set -uo pipefail
ROOT=/mnt/d/work/IdeaProjects/car-monit-backend-new/runtime-logs
TOOLS=/home/dev/tools
OUT=/home/dev/local-auth-retest
mkdir -p "$OUT/logs" "$OUT/contract-reports" "$OUT/load-reports" /home/ruoyi/logs 2>/dev/null || true
JUNIT=$TOOLS/junit-platform-console-standalone.jar
JAR=/home/dev/local-package/backend-master/ruoyi-admin/target/ruoyi-admin.jar
EP=/mnt/d/work/IdeaProjects/car-monit-backend-new/scripts/v3/ops/parity/endpoints/backend-full.txt
[ -f "$JAR" ] || { echo NO_JAR; exit 2; }
[ -f "$JUNIT" ] || { echo NO_JUNIT; exit 2; }
[ -f "$EP" ] || { echo NO_ENDPOINTS; exit 2; }
for i in $(seq 1 30); do (echo > /dev/tcp/127.0.0.1/3307) >/dev/null 2>&1 && break; sleep 1; done
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
export TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef
java -jar "$JAR" --server.port=19903 --spring.main.allow-circular-references=true --spring.main.lazy-initialization=true --spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration > "$OUT/app.log" 2>&1 &
echo $! > "$OUT/app.pid"
READY=0
for i in $(seq 1 180); do
  if (echo > /dev/tcp/127.0.0.1/19903) >/dev/null 2>&1; then READY=1; echo "SERVICE_READY after ${i}s"; break; fi
  if ! kill -0 "$(cat "$OUT/app.pid")" 2>/dev/null; then echo SERVICE_EXITED; tail -80 "$OUT/app.log"; exit 1; fi
  sleep 1
done
[ "$READY" = 1 ] || { echo SERVICE_TIMEOUT; tail -80 "$OUT/app.log"; exit 1; }
TOKEN=$(python3 "$ROOT/junit-auth-token.py" --base-url "$BASE_URL")
[ -n "$TOKEN" ] || { echo NO_TOKEN; exit 1; }
export ENDPOINT_HEADERS="Authorization: Bearer ${TOKEN}"
python3 "$ROOT/generate_junit_suite.py" --endpoints "$EP" --out "$OUT/generated"
mkdir -p "$OUT/classes"
javac -encoding UTF-8 -source 8 -target 8 -cp "$JUNIT" -d "$OUT/classes" "$OUT"/generated/*.java
java -jar "$JUNIT" execute --class-path "$OUT/classes" --select-class com.ruoyi.parity.generated.EndpointContractTest --details=summary --reports-dir "$OUT/contract-reports" 2>&1 | tee "$OUT/contract.log"
LOAD_THREADS=4 LOAD_SECONDS=15 LOAD_WARMUP_SECONDS=1 java -jar "$JUNIT" execute --class-path "$OUT/classes" --select-class com.ruoyi.parity.generated.EndpointLoadTest --details=summary --reports-dir "$OUT/load-reports" 2>&1 | tee "$OUT/load.log"
kill "$(cat "$OUT/app.pid")" 2>/dev/null || true
echo LOCAL_AUTH_RETEST_DONE
