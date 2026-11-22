#!/usr/bin/env bash

# @description 历史脚本 step11c-rebuild.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash step11c-rebuild.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -euo pipefail

B=/home/dev/k3s-build

JDK=/home/dev/.cache/ci-toolchain/jdk-25.0.5+8

WORK=$B/slim

MODS="java.base,java.desktop,java.instrument,java.logging,java.management,java.naming,java.net.http,java.prefs,java.rmi,java.security.jgss,java.security.sasl,java.sql,java.sql.rowset,java.transaction.xa,java.xml,java.xml.crypto,jdk.unsupported,jdk.crypto.ec,jdk.crypto.cryptoki,jdk.management,jdk.management.agent,java.compiler,jdk.attach,jdk.jfr,jdk.net"

echo "=== rebuild jlink runtime with jdk.net ==="

rm -rf "$WORK/jre"

"$JDK/bin/jlink" --add-modules "$MODS" --output "$WORK/jre" --strip-debug --no-man-pages --no-header-files --compress=zip-9

du -sh "$WORK/jre"



echo "=== fontconfig.properties (Java built-in font mapping, no native fontconfig needed) ==="

cat > "$WORK/fonts/fontconfig.properties" <<'EOF'

version=1

allfonts.plain=DejaVuSans

allfonts.bold=DejaVuSans

allfonts.italic=DejaVuSans

allfonts.bolditalic=DejaVuSans

filename.DejaVuSans=/opt/jre/lib/fonts/DejaVuSans.ttf

EOF



echo "=== copy rebuilt slim jars ==="

cp /mnt/d/work/IdeaProjects/car-monit-api-jdk17/pro-business-api/target/pro-business-api-1.0.jar "$WORK/api.jar"

cp /mnt/d/work/IdeaProjects/car-monit-backend-jdk17/ruoyi-admin/target/ruoyi-admin.jar "$WORK/backend.jar"

ls -lh "$WORK/api.jar" "$WORK/backend.jar"



echo "=== rebuild images ==="

for s in api backend; do

  cat > "$WORK/Dockerfile.$s" <<EOF

FROM car-monit-sys:local

COPY jre /opt/jre

COPY $s.jar /app/app.jar

COPY fonts/DejaVuSans.ttf /opt/jre/lib/fonts/DejaVuSans.ttf

COPY fonts/fontconfig.properties /opt/jre/lib/fontconfig.properties

ENV JAVA_HOME=/opt/jre

ENV PATH=/opt/jre/bin:/usr/bin:/bin

WORKDIR /app

ENTRYPOINT ["/opt/jre/bin/java"]

EOF

  docker build -q -t "car-monit-$s:slim" -f "$WORK/Dockerfile.$s" "$WORK" | tail -1

done

docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -E 'car-monit-(api|backend|sys)' | sort

echo "=== jdk.net present ==="

docker run --rm --entrypoint sh car-monit-api:slim -c 'ls /opt/jre/lib/modules >/dev/null && /opt/jre/bin/java --list-modules | grep -E "jdk.net|java.desktop|java.sql"'

