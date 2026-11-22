#!/usr/bin/env bash

# @description 历史脚本 step11-slim-image.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash step11-slim-image.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -euo pipefail

B=/home/dev/k3s-build

JDK=/home/dev/.cache/ci-toolchain/jdk-25.0.5+8

WORK=$B/slim

rm -rf "$WORK"; mkdir -p "$WORK/libs" "$WORK/jre"



echo "=== 1) extract nested jars for jdeps ==="

for j in api backend; do

  unzip -qq -o "$B/$j.jar" 'BOOT-INF/lib/*' -d "$WORK/x-$j"

  cp "$WORK/x-$j"/BOOT-INF/lib/*.jar "$WORK/libs/" 2>/dev/null || true

done

echo "nested jars=$(find "$WORK/libs" -name '*.jar' | wc -l)"



echo "=== 2) compute JDK modules via jdeps ==="

MODS=$(find "$WORK/libs" -name '*.jar' -print0 | xargs -0 "$JDK/bin/jdeps" --ignore-missing-deps --multi-release 25 --print-module-deps 2>/dev/null | tr ',' '\n' | sort -u | grep -v '^$' | paste -sd,)

echo "jdeps modules: $MODS"

EXTRA="java.desktop,java.instrument,java.management,java.naming,java.sql,java.xml,java.logging,java.net.http,java.prefs,java.rmi,java.security.jgss,java.security.sasl,java.transaction.xa,java.xml.crypto,jdk.unsupported,jdk.crypto.ec,jdk.crypto.cryptoki,jdk.management,jdk.management.agent,java.sql.rowset"

ALL=$(echo "$MODS,$EXTRA" | tr ',' '\n' | sort -u | grep -v '^$' | paste -sd,)

echo "jlink modules: $ALL"

"$JDK/bin/jlink" --add-modules "$ALL" --output "$WORK/jre" \

  --strip-debug --no-man-pages --no-header-files --compress=zip-9 2>&1 | head -5

du -sh "$WORK/jre"

"$WORK/jre/bin/java" --version 2>&1 | head -2



echo "=== 3) flatten a minimal glibc system base (strip MySQL server binaries) ==="

docker rm -f slim-base-tmp >/dev/null 2>&1 || true

docker run -d --name slim-base-tmp --entrypoint sleep mysql:8.0.30 3600 >/dev/null

docker exec slim-base-tmp sh -c 'rm -rf /var/lib/mysql /usr/lib64/mysql /usr/share/mysql /usr/bin/mysql* /usr/sbin/mysqld /usr/bin/mysqld* /etc/my.cnf* /docker-entrypoint-initdb.d /usr/local/bin/docker-entrypoint.sh /var/log/mysqld.log' 2>/dev/null || true

docker export slim-base-tmp | docker import - car-monit-sys:local >/dev/null

docker rm -f slim-base-tmp >/dev/null 2>&1 || true

docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -E 'car-monit-sys|mysql:8.0.30'



echo "=== 4) fonts (offline, from WSL) ==="

mkdir -p "$WORK/fonts"

cp /usr/share/fonts/dejavu/DejaVuSans.ttf "$WORK/fonts/" 2>/dev/null || true



echo "=== 5) build slim images ==="

cat > "$WORK/Dockerfile.api" <<'EOF'

FROM car-monit-sys:local

COPY jre /opt/jre

COPY api.jar /app/app.jar

COPY fonts/DejaVuSans.ttf /opt/jre/lib/fonts/DejaVuSans.ttf

ENV JAVA_HOME=/opt/jre

ENV PATH=/opt/jre/bin:/usr/bin:/bin

WORKDIR /app

ENTRYPOINT ["/opt/jre/bin/java"]

EOF

cat > "$WORK/Dockerfile.backend" <<'EOF'

FROM car-monit-sys:local

COPY jre /opt/jre

COPY backend.jar /app/app.jar

COPY fonts/DejaVuSans.ttf /opt/jre/lib/fonts/DejaVuSans.ttf

ENV JAVA_HOME=/opt/jre

ENV PATH=/opt/jre/bin:/usr/bin:/bin

WORKDIR /app

ENTRYPOINT ["/opt/jre/bin/java"]

EOF

# copy slim jars into build context (from Windows worktrees via /mnt/d)

cp /mnt/d/work/IdeaProjects/car-monit-api-jdk17/pro-business-api/target/pro-business-api-1.0.jar "$WORK/api.jar"

cp /mnt/d/work/IdeaProjects/car-monit-backend-jdk17/ruoyi-admin/target/ruoyi-admin.jar "$WORK/backend.jar"

docker build -q -t car-monit-api:slim -f "$WORK/Dockerfile.api" "$WORK"

docker build -q -t car-monit-backend:slim -f "$WORK/Dockerfile.backend" "$WORK"

echo "=== 6) size comparison ==="

docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -E 'car-monit-(api|backend|sys|jre)' | sort

