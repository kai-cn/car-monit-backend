#!/usr/bin/env bash

# @description 历史脚本 step2-build.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash step2-build.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -euo pipefail



echo "=== restart redis with protected-mode no (local-only test cache) ==="

redis-cli -h 127.0.0.1 -p 6380 shutdown nosave >/dev/null 2>&1 || true

sleep 1

redis-server --bind 0.0.0.0 --port 6380 --protected-mode no \

  --daemonize yes --save '' --appendonly no --maxmemory 64mb --maxmemory-policy allkeys-lru

sleep 1

redis-cli -h 127.0.0.1 -p 6380 ping



echo "=== base image OS check ==="

docker run --rm --entrypoint sh mysql:8.0.30 -c 'cat /etc/os-release | head -3; ldd --version | head -1'



BUILD=/home/dev/k3s-build

rm -rf "$BUILD"

mkdir -p "$BUILD"

echo "=== copy JDK + jars into build context ==="

cp -a /home/dev/.cache/ci-toolchain/jdk-17.0.21+9 "$BUILD/jdk"

cp /mnt/d/work/IdeaProjects/car-monit-backend-jdk17/ruoyi-admin/target/ruoyi-admin.jar "$BUILD/backend.jar"

cp /mnt/d/work/IdeaProjects/car-monit-api-jdk17/pro-business-api/target/pro-business-api-1.0.jar "$BUILD/api.jar"

du -sh "$BUILD"/*



cat > "$BUILD/Dockerfile.base" <<'EOF'

FROM mysql:8.0.30

COPY jdk /opt/jdk

ENV JAVA_HOME=/opt/jdk

ENV PATH=/opt/jdk/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

EOF

cat > "$BUILD/Dockerfile.backend" <<'EOF'

FROM car-monit-jre17:local

COPY backend.jar /app/app.jar

ENTRYPOINT ["/opt/jdk/bin/java"]

EOF

cat > "$BUILD/Dockerfile.api" <<'EOF'

FROM car-monit-jre17:local

COPY api.jar /app/app.jar

ENTRYPOINT ["/opt/jdk/bin/java"]

EOF



echo "=== docker build ==="

docker build -q -t car-monit-jre17:local -f "$BUILD/Dockerfile.base" "$BUILD"

docker build -q -t car-monit-backend:local -f "$BUILD/Dockerfile.backend" "$BUILD"

docker build -q -t car-monit-api:local -f "$BUILD/Dockerfile.api" "$BUILD"

docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep car-monit



echo "=== verify java inside built image ==="

docker run --rm --entrypoint /opt/jdk/bin/java car-monit-backend:local -version 2>&1 | head -3



echo "=== k3d image import into all 3 nodes ==="

k3d image import car-monit-backend:local car-monit-api:local -c v3 2>&1 | tail -5

