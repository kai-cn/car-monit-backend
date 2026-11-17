#!/usr/bin/env bash
# ======================================================================
# 用途：云 runner 数据库升级验证的“单格”执行器。
# 调用：bash db_cell.sh <app:api|backend> <db:mysql|opengauss> <side:old|new> <jar> <label>
# 说明：
#   - old 侧：启动旧版数据库容器（mysql:8.0 / enmotech/opengauss:3.0.0），加载版本无关夹具。
#   - new 侧：启动新版容器（mysql:9.7 / opengauss/opengauss:7.x），
#             优先从 out/<db>_dump.sql 逻辑迁移还原；无 dump 时回退加载同一夹具。
#   - 两侧都用同一个 jar 与同一份端点清单跑 parity_probe.py，记录连通性/延迟/RSS。
#   - 凭据只从环境变量读取（CI_DB_PASSWORD），不写入脚本、文档或日志。
# ======================================================================
set -euo pipefail

APP="${1:?app required}"
DB="${2:?db required}"
SIDE="${3:?side required}"
JAR="${4:?jar required}"
LABEL="${5:?label required}"

PW="${CI_DB_PASSWORD:?CI_DB_PASSWORD required}"
PORT_HTTP=19903
MYSQL_C=127.0.0.1
PG_C=127.0.0.1
SQLDIR="scripts/v3/ops/parity/sql"
ENDPOINTS="scripts/v3/ops/parity/endpoints/${APP}.txt"
OUT="out"
mkdir -p "$OUT"

log() { echo "[db_cell $APP/$DB/$SIDE] $*"; }

wait_tcp() {
  local h="$1" p="$2" n="${3:-90}"
  for i in $(seq 1 "$n"); do
    (echo >"/dev/tcp/$h/$p") >/dev/null 2>&1 && return 0
    sleep 2
  done
  return 1
}

pick_image() {
  # 依次尝试候选 tag，返回第一个可拉取的镜像（抵御 Docker Hub tag 漂移）。
  local candidate
  for candidate in "$@"; do
    if docker pull "$candidate" >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

# ---- 启动 MySQL：old=8.0(mysql_native_password)，new=9.7(caching_sha2_password) ----
start_mysql() {
  local name="$1"; shift
  local image tag extra=""
  image=$(pick_image "$@") || { log "no mysql image available from: $*"; return 1; }
  tag="${image##*:}"
  [ "$tag" = "8.0" ] && extra="--default-authentication-plugin=mysql_native_password"
  docker run -d --name "$name" \
    -e "MYSQL_ROOT_PASSWORD=$PW" -e MYSQL_DATABASE=carmonitdb \
    -p 3306:3306 "$image" $extra
  wait_tcp "$MYSQL_C" 3306 120 || { log "MySQL $tag TCP not ready"; return 1; }
  for i in $(seq 1 20); do
    docker exec "$name" mysql -h127.0.0.1 -P3306 --protocol=TCP -uroot -p"$PW" -e 'select 1' >/dev/null 2>&1 && break
    sleep 3
  done
  docker exec "$name" mysql -uroot -p"$PW" -N -e "select version()" 2>/dev/null | tee "$OUT/${DB}_${SIDE}.version.txt"
}

# ---- 启动 openGauss：old=3.0.0，new=7.x 官方镜像 ----
# 容器内的 gsql 需要 LD_LIBRARY_PATH；不同镜像管理员用户可能是 omm 或 gaussdb。
OG_ADMIN=""
og_sql() {
  # 在容器内以管理员执行一条 SQL（stdin 或 -c），返回 0 才算成功。
  local db="$1"; shift
  docker exec -e PGPASSWORD="$PW" -e LD_LIBRARY_PATH=/usr/local/opengauss/lib \
    "$CNAME" /usr/local/opengauss/bin/gsql -h 127.0.0.1 -p 5432 \
    -U "$OG_ADMIN" -d "$db" -w "$@"
}

detect_og_admin() {
  local u
  for u in omm gaussdb; do
    if docker exec -e PGPASSWORD="$PW" -e LD_LIBRARY_PATH=/usr/local/opengauss/lib \
        "$CNAME" /usr/local/opengauss/bin/gsql -h 127.0.0.1 -p 5432 \
        -U "$u" -d postgres -w -Atc 'select 1' >/dev/null 2>&1; then
      OG_ADMIN="$u"
      echo "$u" > "$OUT/${DB}_admin.txt"
      log "openGauss admin user = $u"
      return 0
    fi
  done
  return 1
}

start_opengauss() {
  local name="$1"; shift
  local image
  image=$(pick_image "$@") || { log "no opengauss image available from: $*"; return 1; }
  docker run -d --name "$name" --privileged --shm-size=512m \
    -e "GS_PASSWORD=$PW" -p 5432:5432 "$image"
  wait_tcp "$PG_C" 5432 180 || { log "openGauss $image TCP not ready"; return 1; }
  # 等待容器内部 gsql 可用（首次初始化较慢）。
  local i
  for i in $(seq 1 30); do
    docker exec "$name" /usr/local/opengauss/bin/gsql --version >/dev/null 2>&1 && break
    sleep 3
  done
  CNAME="$name" detect_og_admin || { log "cannot detect openGauss admin user"; return 1; }
  og_sql postgres -Atc 'select version()' > "$OUT/${DB}_${SIDE}.version.txt" 2>/dev/null || \
    { log "cannot read openGauss version"; return 1; }
  og_sql postgres -c 'CREATE DATABASE "RuoYi"' >/dev/null 2>&1 || \
    log "RuoYi DB may already exist; continuing"
}

load_mysql_fixture() {
  local name="$1"
  # api 只需字典表；backend 需全量 schema+seed。
  for i in $(seq 1 10); do
    if [ "$APP" = "backend" ]; then
      docker exec -i "$name" mysql -uroot -p"$PW" -D carmonitdb < "$SQLDIR/schema_carmonitdb.sql" >/dev/null 2>&1 && \
      docker exec -i "$name" mysql -uroot -p"$PW" -D carmonitdb < "$SQLDIR/seed_carmonitdb.sql" >/dev/null 2>&1 && break
    else
      docker exec -i "$name" mysql -uroot -p"$PW" -D carmonitdb < "$SQLDIR/mysql_dict.sql" >/dev/null 2>&1 && break
    fi
    log "mysql fixture load retry $i"; sleep 3
  done
}

load_pg_fixture() {
  # 把版本无关的 schema/seed 拷进容器，用容器内 gsql 加载（宿主 psql16 无法认证 openGauss sha256）。
  gunzip -c "$SQLDIR/seed_jl_data01.sql.gz" > /tmp/dbupgrade_seed.sql
  docker cp "$SQLDIR/schema_jl_data01.sql" "$CNAME:/tmp/schema.sql" >/dev/null
  docker cp /tmp/dbupgrade_seed.sql "$CNAME:/tmp/seed.sql" >/dev/null
  og_sql RuoYi -v ON_ERROR_STOP=1 -f /tmp/schema.sql >/dev/null || { log "schema load failed"; return 1; }
  og_sql RuoYi -v ON_ERROR_STOP=1 -f /tmp/seed.sql >/dev/null || { log "seed load failed"; return 1; }
  og_sql RuoYi -Atc 'select count(*) from jl_data01.ods_szdn_gantry' \
    > "$OUT/${DB}_${SIDE}.rows.txt" 2>/dev/null || { log "row check failed"; return 1; }
  log "gantry rows: $(cat "$OUT/${DB}_${SIDE}.rows.txt")"
}

restore_dump() {
  local name="$1"
  local dump="out/${DB}_dump.sql"
  if [ ! -s "$dump" ]; then
    log "no dump at $dump -> fallback to same fixture"
    return 2
  fi
  if [ "$DB" = "mysql" ]; then
    docker exec -i "$name" mysql -uroot -p"$PW" -D carmonitdb < "$dump" >/dev/null 2>&1
  else
    docker cp "$dump" "$name:/tmp/dump.sql" >/dev/null
    docker exec -e PGPASSWORD="$PW" -e LD_LIBRARY_PATH=/usr/local/opengauss/lib \
      "$name" /usr/local/opengauss/bin/gsql -h 127.0.0.1 -p 5432 \
      -U "$OG_ADMIN" -d RuoYi -w -v ON_ERROR_STOP=1 -f /tmp/dump.sql >/dev/null 2>&1
  fi
}

# ---- 采集容器资源占用（在 app 探针期间由后台采样，此处做一次即时快照） ----
stats() {
  local container="$1"
  docker stats --no-stream --format \
    '{"cpu":"{{.CPUPerc}}","mem":"{{.MemUsage}}","mem_pct":"{{.MemPerc}}"}' "$container" \
    > "$OUT/${DB}_${SIDE}.stats.json" 2>/dev/null || echo '{}' > "$OUT/${DB}_${SIDE}.stats.json"
}

probe() {
  local url_mysql="jdbc:mysql://127.0.0.1:3306/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=GMT%2B8&allowMultiQueries=true"
  local url_pg="jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&serverTimezone=Asia/Shanghai"
  local url_dict="jdbc:mysql://127.0.0.1:3306/carmonitdb?useUnicode=true&characterEncoding=UTF-8&useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai&connectTimeout=3000&socketTimeout=3000"
  if [ "$APP" = "api" ]; then
    local pg_user="postgres"
    [ "$DB" = "opengauss" ] && pg_user="${OG_ADMIN:-omm}"
    SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL="$url_pg" \
    SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME="$pg_user" \
    SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$PW" \
    CARMONIT_MYSQL_HOST="$MYSQL_C" CARMONIT_MYSQL_PORT=3306 \
    CARMONIT_MYSQL_USERNAME=root CARMONIT_MYSQL_PASSWORD="$PW" \
    TRAFFIC_PLATE_COLOR_DICT_URL="$url_dict" \
    TRAFFIC_PLATE_COLOR_DICT_USERNAME=root TRAFFIC_PLATE_COLOR_DICT_PASSWORD="$PW" \
    SPRING_DATA_REDIS_HOST=127.0.0.1 SPRING_DATA_REDIS_PORT=6379 \
    SPRING_REDIS_HOST=127.0.0.1 SPRING_REDIS_PORT=6379 \
    EXPORT_DOWNLOAD_SECRET=dbupgrade-ci-secret \
    python scripts/v3/ops/parity/parity_probe.py \
      --variant jar --label "$LABEL" --cmd "java -jar $JAR --server.port=$PORT_HTTP" \
      --port "$PORT_HTTP" --endpoints "$ENDPOINTS" --out "$OUT/${SIDE}.json" \
      --mode full --check-stability --ready-timeout 300
    python scripts/v3/ops/dbupgrade/gate.py --old "$OUT/${SIDE}.json" --new "$OUT/${SIDE}.json"
  else
    SPRING_DATASOURCE_DRUID_MASTER_URL="$url_mysql" \
    SPRING_DATASOURCE_DRUID_MASTER_USERNAME=root \
    SPRING_DATASOURCE_DRUID_MASTER_PASSWORD="$PW" \
    SPRING_DATASOURCE_DRUID_MASTER_DRIVERCLASSNAME=com.mysql.cj.jdbc.Driver \
    SPRING_DATA_REDIS_HOST=127.0.0.1 SPRING_DATA_REDIS_PORT=6379 \
    SPRING_REDIS_HOST=127.0.0.1 SPRING_REDIS_PORT=6379 \
    TOKEN_SECRET=dbupgrade-ci-secret EXPORT_DOWNLOAD_SECRET=dbupgrade-ci-secret \
    python scripts/v3/ops/parity/parity_probe.py \
      --variant jar --label "$LABEL" --cmd "java -jar $JAR --server.port=$PORT_HTTP" \
      --port "$PORT_HTTP" --endpoints "$ENDPOINTS" --out "$OUT/${SIDE}.json" \
      --mode full --check-stability --ready-timeout 300
    python scripts/v3/ops/dbupgrade/gate.py --old "$OUT/${SIDE}.json" --new "$OUT/${SIDE}.json"
  fi
}

# ================= 主流程 =================
CNAME="${DB}-${SIDE}"

if [ "$DB" = "mysql" ]; then
  if [ "$SIDE" = "old" ]; then
    start_mysql "$CNAME" "mysql:8.0"
    load_mysql_fixture "$CNAME"
  else
    start_mysql "$CNAME" "mysql:9.7" "mysql:9.7.4" "mysql:9.7.3"
    restore_dump "$CNAME" || load_mysql_fixture "$CNAME"
  fi
else
  if [ "$SIDE" = "old" ]; then
    start_opengauss "$CNAME" "enmotech/opengauss:3.0.0"
    load_pg_fixture
  else
    start_opengauss "$CNAME" "opengauss/opengauss:latest" "opengauss/opengauss:7.0.0-RC3.B025"
    restore_dump "$CNAME" || load_pg_fixture
  fi
  # api 主库之外还需要字典 MySQL：未做版本变量，固定 8.0 隔离变量。
  if [ "$APP" = "api" ]; then
    docker run -d --name my-dict -e "MYSQL_ROOT_PASSWORD=$PW" -e MYSQL_DATABASE=carmonitdb \
      -p 3306:3306 mysql:8.0 --default-authentication-plugin=mysql_native_password >/dev/null
    wait_tcp "$MYSQL_C" 3306 120 || true
    docker exec -i my-dict mysql -uroot -p"$PW" -D carmonitdb < "$SQLDIR/mysql_dict.sql" >/dev/null 2>&1 || true
  fi
fi

# api-mysql 格：主库用 postgres:16 等价替代（与既有 parity 口径一致），隔离 MySQL 变量。
if [ "$APP" = "api" ] && [ "$DB" = "mysql" ]; then
  docker run -d --name pg-standin -e "POSTGRES_PASSWORD=$PW" -e POSTGRES_DB=RuoYi \
    -p 5432:5432 postgres:16-alpine >/dev/null
  wait_tcp "$PG_C" 5432 120 || true
  export PGPASSWORD="$PW"
  gunzip -c "$SQLDIR/seed_jl_data01.sql.gz" > /tmp/dbupgrade_seed.sql
  psql -h "$PG_C" -p 5432 -U postgres -d RuoYi -v ON_ERROR_STOP=1 -f "$SQLDIR/schema_jl_data01.sql" >/dev/null 2>&1 || true
  psql -h "$PG_C" -p 5432 -U postgres -d RuoYi -v ON_ERROR_STOP=1 -f /tmp/dbupgrade_seed.sql >/dev/null 2>&1 || true
fi

# backend 需要 redis；api 也用 redis。两侧共享同一容器，避免重名失败。
if ! docker ps -a --format '{{.Names}}' | grep -qx rd; then
  docker run -d --name rd -p 6379:6379 redis:7-alpine >/dev/null
fi
wait_tcp 127.0.0.1 6379 30 || true
sudo mkdir -p /home/ruoyi/logs /home/ruoyi/uploadPath 2>/dev/null || true
sudo chown -R "$(id -u):$(id -g)" /home/ruoyi 2>/dev/null || true

# 探针期间持续采样 DB 容器资源，取最后一次快照（避免单点采样偏差）。
( for i in $(seq 1 120); do stats "$CNAME"; sleep 3; done ) &
STATS_PID=$!
probe
kill "$STATS_PID" 2>/dev/null || true
stats "$CNAME"
log "side done; evidence in $OUT/${SIDE}.json / ${DB}_${SIDE}.stats.json"
