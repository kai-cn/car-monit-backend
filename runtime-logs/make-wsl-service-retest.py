#!/usr/bin/env python3

"""
@description 历史脚本 make-wsl-service-retest.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python make-wsl-service-retest.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Docker CLI 与已启动的守护进程；Java 运行时；Python 3 标准库及脚本原有第三方依赖

Idea:


- avoid line-ending/encoding issues by generating the script from Python


- keep all comments ASCII so shell parsing stays deterministic


- write to runtime-logs and print size for immediate verification
"""
from pathlib import Path



SCRIPT = r'''#!/usr/bin/env bash

# Purpose: run locally packaged backend jar against WSL Docker MySQL/Redis.

# Idea: start Redis, run jar with local DSN, generate JUnit suites, run contract and load tests.

# Risk: starts a local process on 127.0.0.1:19903; writes evidence under /home/dev.

set -uo pipefail

ROOT=/mnt/d/work/runtime-logs

OUT=/home/dev/wsl-service-retest

mkdir -p "$OUT/logs" /home/ruoyi/logs 2>/dev/null || true

JUNIT=$ROOT/junit-platform-console-standalone.jar

JAR=/home/dev/local-package/backend-master/ruoyi-admin/target/ruoyi-admin.jar

EP=/mnt/d/work/IdeaProjects/car-monit-backend-new/scripts/v3/ops/parity/endpoints/backend-full.txt

if [ ! -f "$JAR" ]; then echo "NO_JAR $JAR" >&2; exit 2; fi

if ! docker ps --format '{{.Names}}' | grep -q '^redis_wsl$'; then

  docker run -d --name redis_wsl -p 6379:6379 redis:7-alpine >/dev/null

fi

for i in $(seq 1 30); do docker exec redis_wsl redis-cli ping >/dev/null 2>&1 && break; sleep 1; done

export BASE_URL=http://127.0.0.1:19903

export OUT_DIR=$OUT

export LOG_PATH=$OUT/logs

export HTTP_TIMEOUT_MS=60000

export SPRING__DATASOURCE__DRUID__MASTER__URL='jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8'

export SPRING__DATASOURCE__DRUID__MASTER__USERNAME=root

export SPRING__DATASOURCE__DRUID__MASTER__PASSWORD=root

export SPRING__REDIS__HOST=127.0.0.1

export SPRING__REDIS__PORT=6379

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

[ "$READY" = 1 ] || { echo SERVICE_TIMEOUT; tail -80 "$OUT/app.log"; exit 1; }

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

echo LOCAL_SERVICE_RETEST_DONE

'''



p = Path(r'D:\work\runtime-logs\wsl-local-service-retest2.sh')

p.write_text(SCRIPT, encoding='utf-8')

print('WROTE', p, len(p.read_bytes()))

