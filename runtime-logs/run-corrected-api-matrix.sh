#!/usr/bin/env bash
# @description 按修正后的 api Java 基准和真实主键端点，串行运行 api Python/Go/Rust/C++ 实测与结构比较。
# @author Tencent Hunyuan Hy
# @date 2026-11-24 20:10:00
# @usage bash runtime-logs/run-corrected-api-matrix.sh
# @dependencies Python3、Go、Rust、CMake、本地 PostgreSQL/Redis/ES。
# NOTE: 比较器以 Java 基准 code 与 JSON 结构为准，业务错误也必须与原 Java 一致。
set -uo pipefail
B=/home/dev/IdeaProjects/car-monit-backend
A=/home/dev/IdeaProjects/car-monit-api
L="$B/runtime-logs"
EP="$L/real-key-endpoints/api-read-realkey.txt"
BASE="$L/local-parity-matrix/api/java-correct-realkey/junit-contract.json"

export CARMONIT_ADMIN_USER=admin TOKEN__SECRET=
export CARMONIT_LOCAL_PARITY=1
: "${CARMONIT_ADMIN_PASSWORD:?set CARMONIT_ADMIN_PASSWORD in environment}"
export TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL='jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false'
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=postgres SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD=postgres
export HENGDA__SECRET='pytest-only-hengda-signing-key-4d8e1a6b2f9c0357' ELASTICSEARCH_HOST=172.18.0.1 ELASTICSEARCH_PORT=9200
export APP_SERVER_PORT=19903 APP_SERVER__PORT=19903 APP_REDIS_HOST=127.0.0.1 APP_REDIS_PORT=6379 APP_REDIS__HOST=127.0.0.1 APP_REDIS__PORT=6379
export APP_TOKEN__SECRET='anVuaXQtY2xvdWQtc2VjcmV0LWRldGVybWluaXN0aWMtMDEyMzQ1Njc4OWFiY2RlZg=='
export APP_DATABASE__URL='jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false'
export APP_DATABASE__USERNAME=postgres APP_DATABASE__PASSWORD=postgres APP_KAFKA_BOOTSTRAP_SERVERS=''
export APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL='jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false'
export APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=postgres APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD=postgres
export CM_SERVER_PORT=19903 CM_PG_HOST=127.0.0.1 CM_PG_PORT=5432 CM_PG_USER=postgres CM_PG_PASSWORD=postgres CM_PG_DATABASE=RuoYi CM_KAFKA_ENABLED=false CM_KAFKA_BOOTSTRAP='' CM_ES_HOST=127.0.0.1

run_one() {
  local lang="$1" out="$2" start="$3"
  echo "=== api/$lang ==="
  fuser -k 19903/tcp 2>/dev/null || true
  pkill -f 'local-parity-runner.py' 2>/dev/null || true
  pkill -f '/home/dev/IdeaProjects/car-monit-backend/car-monit-go/bin/car-monit-go' 2>/dev/null || true
  pkill -f '/home/dev/IdeaProjects/car-monit-backend/car-monit-rust/target/release/car-monit-rust' 2>/dev/null || true
  pkill -f '/home/dev/IdeaProjects/car-monit-backend/car-monit-cpp/build-local/car-monit-cpp' 2>/dev/null || true
  pkill -f '/home/dev/IdeaProjects/car-monit-api/car-monit-api-go/bin/car-monit-api' 2>/dev/null || true
  pkill -f '/home/dev/IdeaProjects/car-monit-api/car-monit-api-rust/target/release/car-monit-api-rust' 2>/dev/null || true
  pkill -f '/home/dev/IdeaProjects/car-monit-api/car-monit-api-cpp/build-linux-kafka/car-monit-api' 2>/dev/null || true
  sleep 2
  rm -rf "$out"
  python3 "$L/local-parity-runner.py" --app api --lang "$lang" --endpoints "$EP" --out "$out" --start "$start" > "$out.runner.log" 2>&1
  if [ -f "$out/junit-contract.json" ]; then
    python3 "$L/analyze-endpoint-code.py" "$out/junit-contract.json" "$out/endpoint-code-analysis.json" | tail -2
    python3 "$L/compare-json-structure.py" "$BASE" "$out/junit-contract.json" "$out/structure-compare.json"
  else
    echo NO_CONTRACT
    tail -20 "$out.runner.log"
  fi
}

run_one python "$L/local-parity-matrix/api/python-final-correct" "cd $A/car-monit-api-python && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 19903"
run_one go "$L/local-parity-matrix/api/go-final-correct" "cd $A/car-monit-api-go && ./bin/car-monit-api -config configs/config.yaml"
run_one rust "$L/local-parity-matrix/api/rust-final-correct" "cd $A/car-monit-api-rust && ./target/release/car-monit-api-rust"
run_one cpp "$L/local-parity-matrix/api/cpp-final-correct" "cd $A/car-monit-api-cpp && ./build-linux-kafka/car-monit-api --config configs/config.yaml"
