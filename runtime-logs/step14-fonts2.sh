#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -euo pipefail
W=/home/dev/k3s-build/slim
SRC=registry.cn-hangzhou.aliyuncs.com/helowin/oracle_11g:latest
rm -rf "$W/sys"; mkdir -p "$W/sys/lib64" "$W/sys/etc/fonts" "$W/sys/bin" "$W/sys/fonts"
docker rm -f font-src >/dev/null 2>&1 || true
docker create --name font-src --entrypoint sleep "$SRC" 3600 >/dev/null

echo "=== copy REAL .so files (not dangling symlinks) ==="
for pair in \
  "libfontconfig.so.1.4.4:libfontconfig.so.1" \
  "libfreetype.so.6.3.22:libfreetype.so.6" \
  "libpng15.so.15.13.0:libpng15.so.15" \
  "libbz2.so.1.0.6:libbz2.so.1" ; do
  src=${pair%%:*}; dst=${pair##*:}
  if docker cp "font-src:/usr/lib64/$src" "$W/sys/lib64/$dst" 2>/dev/null; then echo "ok $dst"; else echo "missing $src"; fi
done
echo "=== copy full fontconfig configuration ==="
docker cp font-src:/etc/fonts/. "$W/sys/etc/fonts/" 2>/dev/null || true
docker cp font-src:/usr/bin/fc-cache "$W/sys/bin/fc-cache" 2>/dev/null || true
docker cp font-src:/usr/bin/fc-list "$W/sys/bin/fc-list" 2>/dev/null || true
cp /usr/share/fonts/dejavu/DejaVuSans.ttf "$W/sys/fonts/"
docker rm -f font-src >/dev/null 2>&1 || true
find "$W/sys" -maxdepth 2 -type f | head -14

echo "=== rebuild images ==="
for s in api backend; do
  cat > "$W/Dockerfile.$s" <<EOF
FROM car-monit-sys:local
COPY jre /opt/jre
COPY $s.jar /app/app.jar
COPY sys/lib64/ /usr/lib64/
COPY sys/etc/fonts /etc/fonts
COPY sys/bin/fc-cache /usr/bin/fc-cache
COPY sys/bin/fc-list /usr/bin/fc-list
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
echo "=== verify ==="
docker run --rm --entrypoint sh car-monit-backend:slim -c 'fc-list 2>&1 | head -3; ldd /usr/lib64/libfontconfig.so.1 2>&1 | grep "not found" || echo "libfontconfig deps OK"; ldd /usr/lib64/libfreetype.so.6 2>&1 | grep "not found" || echo "libfreetype deps OK"'
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -E 'car-monit-(api|backend):slim'
