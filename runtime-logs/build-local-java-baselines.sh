#!/usr/bin/env bash
# @description 重建 backend/api master 的 Java 可执行 jar，作为 WSL 本地多语言对齐基准。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 16:45:00
# @usage bash runtime-logs/build-local-java-baselines.sh
# @dependencies JDK8、Maven、两仓库 master 工作树。
set -uo pipefail
B=/home/dev/IdeaProjects/car-monit-backend
A=/home/dev/IdeaProjects/car-monit-api
OUT=/home/dev/local-package/current-master
mkdir -p "$OUT/backend" "$OUT/api"

echo "=== build backend master ==="
JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.502.b07-1.oe2403sp4.x86_64 \
PATH=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.502.b07-1.oe2403sp4.x86_64/bin:$PATH \
mvn -B -ntp -DskipTests -Dspring-boot.aot.skip=true -f "$B/pom.xml" -pl ruoyi-admin -am clean package > "$OUT/backend-build.log" 2>&1
echo "BACKEND_BUILD_RC=$?"
cp "$B/ruoyi-admin/target/ruoyi-admin.jar" "$OUT/backend/ruoyi-admin.jar" 2>/dev/null || true

echo "=== build api master ==="
JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.502.b07-1.oe2403sp4.x86_64 \
PATH=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.502.b07-1.oe2403sp4.x86_64/bin:$PATH \
mvn -B -ntp -DskipTests -Dspring-boot.aot.skip=true -f "$A/pom.xml" -pl pro-business-api -am clean package > "$OUT/api-build.log" 2>&1
echo "API_BUILD_RC=$?"
cp "$A/pro-business-api/target/pro-business-api-1.0.jar" "$OUT/api/pro-business-api-1.0.jar" 2>/dev/null || true
ls -lh "$OUT/backend/ruoyi-admin.jar" "$OUT/api/pro-business-api-1.0.jar" 2>/dev/null || true
