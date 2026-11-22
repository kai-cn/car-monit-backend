#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -euo pipefail
B=/home/dev/k3s-build
JDK=/home/dev/.cache/ci-toolchain/jdk-25.0.5+8
WORK=$B/slim
mkdir -p "$WORK/fonts"; rm -rf "$WORK/jre"
echo "=== jdeps on fat jar outer classes only (fast) ==="
"$JDK/bin/jdeps" --ignore-missing-deps --multi-release 25 --print-module-deps "$WORK/api.jar" 2>&1 | head -2 || true
MODS="java.base,java.desktop,java.instrument,java.logging,java.management,java.naming,java.net.http,java.prefs,java.rmi,java.security.jgss,java.security.sasl,java.sql,java.sql.rowset,java.transaction.xa,java.xml,java.xml.crypto,jdk.unsupported,jdk.crypto.ec,jdk.crypto.cryptoki,jdk.management,jdk.management.agent,java.compiler,jdk.attach,jdk.jfr"
echo "modules=$MODS"
"$JDK/bin/jlink" --add-modules "$MODS" --output "$WORK/jre" \
  --strip-debug --no-man-pages --no-header-files --compress=zip-9
du -sh "$WORK/jre"
"$WORK/jre/bin/java" --version 2>&1 | head -2
echo "=== flatten minimal glibc base ==="
docker rm -f slim-base-tmp >/dev/null 2>&1 || true
docker run -d --name slim-base-tmp --entrypoint sleep mysql:8.0.30 3600 >/dev/null
docker exec slim-base-tmp sh -c 'rm -rf /var/lib/mysql /usr/lib64/mysql /usr/share/mysql /usr/bin/mysql* /usr/sbin/mysqld /usr/bin/mysqld* /etc/my.cnf* /docker-entrypoint-initdb.d /usr/local/bin/docker-entrypoint.sh /var/log/mysqld.log' 2>/dev/null || true
docker export slim-base-tmp | docker import - car-monit-sys:local >/dev/null
docker rm -f slim-base-tmp >/dev/null 2>&1 || true
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -E 'car-monit-sys|mysql:8.0.30'
echo "=== fonts ==="
cp /usr/share/fonts/dejavu/DejaVuSans.ttf "$WORK/fonts/" 2>/dev/null || true
ls -lh "$WORK/fonts"
echo "=== build slim images ==="
cp /mnt/d/work/IdeaProjects/car-monit-api-jdk17/pro-business-api/target/pro-business-api-1.0.jar "$WORK/api.jar"
cp /mnt/d/work/IdeaProjects/car-monit-backend-jdk17/ruoyi-admin/target/ruoyi-admin.jar "$WORK/backend.jar"
for s in api backend; do
  cat > "$WORK/Dockerfile.$s" <<EOF
FROM car-monit-sys:local
COPY jre /opt/jre
COPY $s.jar /app/app.jar
COPY fonts/DejaVuSans.ttf /opt/jre/lib/fonts/DejaVuSans.ttf
ENV JAVA_HOME=/opt/jre
ENV PATH=/opt/jre/bin:/usr/bin:/bin
WORKDIR /app
ENTRYPOINT ["/opt/jre/bin/java"]
EOF
  docker build -q -t "car-monit-$s:slim" -f "$WORK/Dockerfile.$s" "$WORK" | tail -1
done
echo "=== size comparison ==="
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -E 'car-monit-(api|backend|sys)' | sort
