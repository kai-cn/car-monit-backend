#!/usr/bin/env bash
# @description 按修正后的 Java 基准和真实主键端点，串行运行 backend/api 各语言实测与结构比较。
# @author Tencent Hunyuan Hy
# @date 2026-11-24 19:50:00
# @usage bash runtime-logs/run-corrected-parity-matrix.sh
# @dependencies Java8、Python3、Go、Rust、CMake、本地数据与 9902 Java 下游。
# NOTE: 所有候选共用同一端点清单；比较器以 Java 基准 code 与 JSON 结构为准，键顺序无关。
set -uo pipefail
B=/home/dev/IdeaProjects/car-monit-backend
A=/home/dev/IdeaProjects/car-monit-api
L="$B/runtime-logs"
EPB="$L/real-key-endpoints/backend-read-realkey.txt"
EPA="$L/real-key-endpoints/api-read-realkey.txt"
BASEB="$L/local-parity-matrix/backend/java-correct-realkey2/junit-contract.json"

export CARMONIT_ADMIN_USER=admin EXPORT_DOWNLOAD_SECRET='local-parity-export-secret-0123456789abcdef'
export CARMONIT_LOCAL_PARITY=1
: "${CARMONIT_ADMIN_PASSWORD:?set CARMONIT_ADMIN_PASSWORD in environment}"
export TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef HENGDA__SECRET='pytest-only-hengda-signing-key-4d8e1a6b2f9c0357'
export SPRING__DATASOURCE__DRUID__MASTER__URL='jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8'
export SPRING__DATASOURCE__DRUID__MASTER__USERNAME=root SPRING__DATASOURCE__DRUID__MASTER__PASSWORD=root
export VEHICLE_MONITOR_BASE_URL=http://127.0.0.1:9902 ELASTICSEARCH_HOST=172.18.0.1 ELASTICSEARCH_PORT=9200
export CARMONIT_DATABASE_DSN='root:root@tcp(127.0.0.1:3307)/carmonitdb?charset=utf8mb4&parseTime=True&loc=Local&multiStatements=true'
export CARMONIT_REDIS_ADDR=127.0.0.1:6379 CARMONIT_SERVER_PORT=19903 CARMONIT_TOKEN_SECRET=junit-cloud-secret-deterministic-0123456789abcdef
export APP_SERVER_PORT=19903 APP_SERVER__PORT=19903 APP_REDIS_HOST=127.0.0.1 APP_REDIS_PORT=6379 APP_REDIS__HOST=127.0.0.1 APP_REDIS__PORT=6379
export APP_TOKEN__SECRET='anVuaXQtY2xvdWQtc2VjcmV0LWRldGVybWluaXN0aWMtMDEyMzQ1Njc4OWFiY2RlZg=='
export APP_DATABASE__URL='jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8'
export APP_DATABASE__USERNAME=root APP_DATABASE__PASSWORD=root APP_KAFKA_BOOTSTRAP_SERVERS=''
export CM_SERVER_PORT=19903 CM_PG_HOST=127.0.0.1 CM_PG_PORT=5432 CM_PG_USER=postgres CM_PG_PASSWORD=postgres CM_PG_DATABASE=RuoYi
export CM_KAFKA_ENABLED=false CM_KAFKA_BOOTSTRAP='' CM_ES_HOST=127.0.0.1

run_one() {
  local app="$1" lang="$2" ep="$3" out="$4" start="$5"
  echo "=== $app/$lang ==="
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
  python3 "$L/local-parity-runner.py" --app "$app" --lang "$lang" --endpoints "$ep" --out "$out" --start "$start" > "$out.runner.log" 2>&1
  if [ -f "$out/junit-contract.json" ]; then
    python3 "$L/analyze-endpoint-code.py" "$out/junit-contract.json" "$out/endpoint-code-analysis.json" | tail -2
    python3 "$L/compare-json-structure.py" "$BASEB" "$out/junit-contract.json" "$out/structure-compare.json"
  else
    echo NO_CONTRACT
    tail -20 "$out.runner.log"
  fi
}

run_one backend python "$EPB" "$L/local-parity-matrix/backend/python-final" "cd $B/car-monit-py && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 19903"
run_one backend go "$EPB" "$L/local-parity-matrix/backend/go-final" "cd $B/car-monit-go && ./bin/car-monit-go -c configs/config.yaml"
run_one backend rust "$EPB" "$L/local-parity-matrix/backend/rust-final" "cd $B/car-monit-rust && ./target/release/car-monit-rust"
run_one backend cpp "$EPB" "$L/local-parity-matrix/backend/cpp-final" "cd $B/car-monit-cpp && ./build-local/car-monit-cpp --config config"
