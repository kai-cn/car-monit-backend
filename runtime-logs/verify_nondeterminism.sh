#!/bin/bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only verification of a security or build invariant.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Hypothesis: /base/vehicleweight/map & /base/feeGantry/list return non-deterministic rows
# (LIMIT without ORDER BY) -> same variant yields different bodies across calls.
set -uo pipefail
NATIVE=/mnt/d/work/runtime-logs/cicd-artifacts/native-api-jdk25-115MB/api-jdk25-linux-amd64.bin
chmod +x "$NATIVE"
GS_PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -1)
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL="jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&serverTimezone=Asia/Shanghai"
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb
export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$GS_PASS"
export EXPORT_DOWNLOAD_SECRET=x

"$NATIVE" --server.port=19902 >/tmp/nd.log 2>&1 &
P=$!
for i in $(seq 1 60); do (echo > /dev/tcp/127.0.0.1/19902) 2>/dev/null && break; sleep 1; done

for ep in /base/vehicleweight/map /base/feeGantry/list; do
  echo "=== $ep: 5 calls on the SAME native process ==="
  for k in 1 2 3 4 5; do
    curl -s "http://127.0.0.1:19902$ep" | sha256sum | cut -c1-16
  done
done
kill $P 2>/dev/null; wait $P 2>/dev/null
