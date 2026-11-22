#!/usr/bin/env bash

# @description 历史脚本 step13-fonts.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash step13-fonts.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -euo pipefail

W=/home/dev/k3s-build/slim

SRC=registry.cn-hangzhou.aliyuncs.com/helowin/oracle_11g:latest

mkdir -p "$W/sys/lib64" "$W/sys/etc" "$W/sys/bin" "$W/sys/fonts"

echo "=== extract native fontconfig from oracle_11g (glibc 2.17, compatible with OL8 2.28) ==="

docker rm -f font-src >/dev/null 2>&1 || true

docker create --name font-src --entrypoint sleep "$SRC" 3600 >/dev/null

for f in libfontconfig.so.1 libfreetype.so.6 libpng15.so.15 libbz2.so.1 libharfbuzz.so.0; do

  docker cp "font-src:/usr/lib64/$f" "$W/sys/lib64/$f" 2>/dev/null || echo "skip $f"

done

docker cp font-src:/etc/fonts "$W/sys/etc/fonts" 2>/dev/null || true

docker cp font-src:/usr/bin/fc-cache "$W/sys/bin/fc-cache" 2>/dev/null || true

cp /usr/share/fonts/dejavu/DejaVuSans.ttf "$W/sys/fonts/"

docker rm -f font-src >/dev/null 2>&1 || true

echo "=== files ==="

find "$W/sys" -maxdepth 3 -type f | head -20



echo "=== rebuild images with native fontconfig ==="

for s in api backend; do

  cat > "$W/Dockerfile.$s" <<EOF

FROM car-monit-sys:local

COPY jre /opt/jre

COPY $s.jar /app/app.jar

COPY sys/lib64/ /usr/lib64/

COPY sys/etc/fonts /etc/fonts

COPY sys/bin/fc-cache /usr/bin/fc-cache

COPY sys/fonts/DejaVuSans.ttf /usr/share/fonts/dejavu/DejaVuSans.ttf

ENV JAVA_HOME=/opt/jre

ENV PATH=/opt/jre/bin:/usr/bin:/bin

ENV FONTCONFIG_PATH=/etc/fonts

WORKDIR /app

RUN fc-cache -f /usr/share/fonts >/dev/null 2>&1 || true

ENTRYPOINT ["/opt/jre/bin/java"]

EOF

  docker build -q -t "car-monit-$s:slim" -f "$W/Dockerfile.$s" "$W" | tail -1

done

echo "=== verify fontconfig inside image ==="

docker run --rm --entrypoint sh car-monit-backend:slim -c 'fc-list 2>&1 | head -3; ldd /usr/lib64/libfontconfig.so.1 2>&1 | grep "not found" || echo "all libs resolved"'

docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -E 'car-monit-(api|backend):slim'

