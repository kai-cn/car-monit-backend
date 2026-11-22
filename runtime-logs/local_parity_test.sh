# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
﻿#!/bin/bash
# Local smoke test of parity_probe.py + parity_compare.py against WSL opengauss+mysql+redis.
set -uo pipefail
PR=/mnt/d/work/runtime-logs
NATIVE="$PR/cicd-artifacts/native-api-jdk25-115MB/api-jdk25-linux-amd64.bin"
JAR="/mnt/d/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api-1.0.jar"
JAVA=/home/dev/tools/mandrel-25/bin/java
EPS="$PR/api-endpoints.txt"
OUT="$PR/parity-local"
mkdir -p "$OUT" && rm -f "$OUT"/*.json "$OUT"/*.log

GS_PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -1)
MY_PASS=$(docker exec mysql_wsl env 2>/dev/null | sed -n 's/^[^=]*MYSQL_ROOT_PASSWORD=//p' | tr -d '\r' | head -1)
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL="jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&serverTimezone=Asia/Shanghai"
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$GS_PASS"
export CARMONIT_MYSQL_HOST=127.0.0.1 CARMONIT_MYSQL_PORT=3307
export CARMONIT_MYSQL_USERNAME=root CARMONIT_MYSQL_PASSWORD="$MY_PASS"
export SPRING_DATA_REDIS_HOST=127.0.0.1 SPRING_DATA_REDIS_PORT=6379
export SPRING_REDIS_HOST=127.0.0.1 SPRING_REDIS_PORT=6379
export EXPORT_DOWNLOAD_SECRET=parity-local-secret

echo "==== probe jar ===="
python3 "$PR/parity_probe.py" --variant jar --label api-local-jdk25 \
  --cmd "$JAVA -jar $JAR --server.port=19903" --port 19903 \
  --endpoints "$EPS" --out "$OUT/jar.json" --mode full --check-stability --ready-timeout 240 2>&1 | tail -3

echo "==== probe native ===="
chmod +x "$NATIVE"
python3 "$PR/parity_probe.py" --variant native --label api-local-jdk25 \
  --cmd "$NATIVE --server.port=19902" --port 19902 \
  --endpoints "$EPS" --out "$OUT/native.json" --mode full --check-stability --ready-timeout 240 2>&1 | tail -3

echo "==== compare ===="
python3 "$PR/parity_compare.py" --baseline "$OUT/jar.json" --candidate "$OUT/native.json" \
  --out "$OUT/report.json" --md "$OUT/report.md" --label api-local-jdk25 2>&1 | tail -5
echo "compare_exit=$?"
