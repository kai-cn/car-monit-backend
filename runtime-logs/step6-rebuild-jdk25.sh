#!/usr/bin/env bash
# @description 历史脚本 step6-rebuild-jdk25.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash step6-rebuild-jdk25.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -euo pipefail
BUILD=/home/dev/k3s-build
echo "=== swap runtime JDK to 25 (compact object headers) ==="
rm -rf "$BUILD/jdk"
cp -a /home/dev/.cache/ci-toolchain/jdk-25.0.5+8 "$BUILD/jdk"
sed -i 's#ENV JAVA_HOME=/opt/jdk#ENV JAVA_HOME=/opt/jdk#' "$BUILD/Dockerfile.base"
cat > "$BUILD/Dockerfile.base" <<'EOF'
FROM mysql:8.0.30
COPY jdk /opt/jdk
ENV JAVA_HOME=/opt/jdk
ENV PATH=/opt/jdk/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
EOF
cat > "$BUILD/Dockerfile.backend" <<'EOF'
FROM car-monit-jre25:local
COPY backend.jar /app/app.jar
ENTRYPOINT ["/opt/jdk/bin/java"]
EOF
cat > "$BUILD/Dockerfile.api" <<'EOF'
FROM car-monit-jre25:local
COPY api.jar /app/app.jar
ENTRYPOINT ["/opt/jdk/bin/java"]
EOF
docker build -q -t car-monit-jre25:local -f "$BUILD/Dockerfile.base" "$BUILD"
docker build -q -t car-monit-backend:local -f "$BUILD/Dockerfile.backend" "$BUILD"
docker build -q -t car-monit-api:local -f "$BUILD/Dockerfile.api" "$BUILD"
docker run --rm --entrypoint /opt/jdk/bin/java car-monit-backend:local -XX:+UseCompactObjectHeaders -version 2>&1 | head -3
echo "=== import into k3d (replaces same tags) ==="
k3d image import car-monit-backend:local car-monit-api:local -c v3 2>&1 | tail -3
