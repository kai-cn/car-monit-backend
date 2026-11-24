#!/usr/bin/env bash
# @description 以真实主键只读端点为统一基准，串行运行 backend/api Java/Python/Go/Rust/C++ 本地实测与结构比较。
# @author Tencent Hunyuan Hy
# @date 2026-11-24 22:30:00
# @usage CARMONIT_ADMIN_PASSWORD=... bash runtime-logs/run-read-only-matrix.sh
# @dependencies 本地数据服务、9902 Java 下游、已构建各语言服务包。
# NOTE: 只读端点仅含列表、分页、主键详情；比较器以 Java 基准 code 与 JSON 结构为准，键顺序无关。
set -uo pipefail
B=/home/dev/IdeaProjects/car-monit-backend
A=/home/dev/IdeaProjects/car-monit-api
L="$B/runtime-logs"
EPB="$L/real-key-endpoints/backend-read-only.txt"
EPA="$L/real-key-endpoints/api-read-only.txt"
BASEB="$L/local-parity-matrix/backend/java-readonly/junit-contract.json"
BASEA="$L/local-parity-matrix/api/java-readonly/junit-contract.json"
: "${CARMONIT_ADMIN_PASSWORD:?set CARMONIT_ADMIN_PASSWORD in environment}"

export CARMONIT_ADMIN_USER=admin EXPORT_DOWNLOAD_SECRET='local-parity-export-secret-0123456789abcdef'
export TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef
export HENGDA__SECRET='pytest-only-hengda-signing-key-4d8e1a6b2f9c0357'
export CARMONIT_LOCAL_PARITY=1
export VEHICLE_MONITOR_BASE_URL=http://127.0.0.1:9902 ELASTICSEARCH_HOST=172.18.0.1 ELASTICSEARCH_PORT=9200
export SPRING__DATASOURCE__DRUID__MASTER__URL='jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8'
export SPRING__DATASOURCE__DRUID__MASTER__USERNAME=root SPRING__DATASOURCE__DRUID__MASTER__PASSWORD=root
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL='jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false'
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=postgres SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD=postgres
export CARMONIT_DATABASE_DSN='root:root@tcp(127.0.0.1:3307)/carmonitdb?charset=utf8mb4&parseTime=True&loc=Local&multiStatements=true'
export CARMONIT_REDIS_ADDR=127.0.0.1:6379 CARMONIT_SERVER_PORT=19903 CARMONIT_TOKEN_SECRET=junit-cloud-secret-deterministic-0123456789abcdef
export APP_SERVER_PORT=19903 APP_SERVER__PORT=19903 APP_REDIS_HOST=127.0.0.1 APP_REDIS_PORT=6379 APP_REDIS__HOST=127.0.0.1 APP_REDIS__PORT=6379
export APP_TOKEN__SECRET='anVuaXQtY2xvdWQtc2VjcmV0LWRldGVybWluaXN0aWMtMDEyMzQ1Njc4OWFiY2RlZg=='
export APP_DATABASE__URL='jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8'
export APP_DATABASE__USERNAME=root APP_DATABASE__PASSWORD=root APP_KAFKA_BOOTSTRAP_SERVERS=''
export APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL='jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false'
export APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=postgres APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD=postgres
export CM_SERVER_PORT=19903 CM_PG_HOST=127.0.0.1 CM_PG_PORT=5432 CM_PG_USER=postgres CM_PG_PASSWORD=postgres CM_PG_DATABASE=RuoYi CM_KAFKA_ENABLED=false CM_KAFKA_BOOTSTRAP='' CM_ES_HOST=127.0.0.1 CM_VEHICLEMONITOR_BASEURL=http://127.0.0.1:9902

stop_service() {
  fuser -k 19903/tcp 2>/dev/null || true
  pkill -f 'local-parity-runner.py' 2>/dev/null || true
  sleep 2
}

run_one() {
  local app="$1" lang="$2" ep="$3" out="$4" start="$5" base="$6"
  echo "=== $app/$lang ==="
  stop_service
  rm -rf "$out"
  python3 "$L/local-parity-runner.py" --app "$app" --lang "$lang" --endpoints "$ep" --out "$out" --start "$start" > "$out.runner.log" 2>&1
  if [ ! -f "$out/junit-contract.json" ]; then echo NO_CONTRACT; tail -20 "$out.runner.log"; return; fi
  python3 "$L/analyze-endpoint-code.py" "$out/junit-contract.json" "$out/endpoint-code-analysis.json" | tail -2
  if [ -n "$base" ] && [ -f "$base" ]; then
    python3 "$L/compare-json-structure.py" "$base" "$out/junit-contract.json" "$out/structure-compare.json"
  fi
}

stop_service
run_one backend java "$EPB" "$L/local-parity-matrix/backend/java-readonly" "java -jar /home/dev/local-package/current-master/backend/ruoyi-admin.jar --server.port=19903 --spring.main.allow-circular-references=true --spring.main.lazy-initialization=true --spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration --spring.datasource.druid.master.url='jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8' --spring.datasource.druid.master.username=root --spring.datasource.druid.master.password=root --spring.datasource.druid.master.driver-class-name=com.mysql.cj.jdbc.Driver --spring.redis.host=127.0.0.1 --spring.redis.port=6379 --token.secret=junit-cloud-secret-deterministic-0123456789abcdef --vehicle-monitor.base-url=http://127.0.0.1:9902 --spring.elasticsearch.uris=http://172.18.0.1:9200" ""
run_one backend python "$EPB" "$L/local-parity-matrix/backend/python-readonly" "cd $B/car-monit-py && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 19903" "$BASEB"
run_one backend go "$EPB" "$L/local-parity-matrix/backend/go-readonly" "cd $B/car-monit-go && ./bin/car-monit-go -c configs/config.yaml" "$BASEB"
run_one backend rust "$EPB" "$L/local-parity-matrix/backend/rust-readonly" "cd $B/car-monit-rust && ./target/release/car-monit-rust" "$BASEB"
run_one backend cpp "$EPB" "$L/local-parity-matrix/backend/cpp-readonly" "cd $B/car-monit-cpp && ./build-local/car-monit-cpp --config config" "$BASEB"

stop_service
run_one api java "$EPA" "$L/local-parity-matrix/api/java-readonly" "java -jar /home/dev/local-package/current-master/api/pro-business-api-1.0.jar --server.port=19903 --spring.main.allow-circular-references=true --spring.main.lazy-initialization=true --spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration --spring.datasource.dynamic.datasource.master.url='jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false' --spring.datasource.dynamic.datasource.master.username=postgres --spring.datasource.dynamic.datasource.master.password=postgres --spring.redis.host=127.0.0.1 --spring.redis.port=6379 --token.secret=junit-cloud-secret-deterministic-0123456789abcdef --spring.elasticsearch.uris=http://172.18.0.1:9200" ""
run_one api python "$EPA" "$L/local-parity-matrix/api/python-readonly" "cd $A/car-monit-api-python && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 19903" "$BASEA"
run_one api go "$EPA" "$L/local-parity-matrix/api/go-readonly" "cd $A/car-monit-api-go && ./bin/car-monit-api -config configs/config.yaml" "$BASEA"
run_one api rust "$EPA" "$L/local-parity-matrix/api/rust-readonly" "cd $A/car-monit-api-rust && ./target/release/car-monit-api-rust" "$BASEA"
run_one api cpp "$EPA" "$L/local-parity-matrix/api/cpp-readonly" "cd $A/car-monit-api-cpp && ./build-linux-kafka/car-monit-api --config configs/config.yaml" "$BASEA"
