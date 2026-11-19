#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== WSL addresses ==="
ip -4 -br addr 2>/dev/null | head -12
echo "=== published-port containers networks ==="
for c in mysql_wsl opengauss; do
  echo -n "$c: "; docker inspect "$c" --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} IP={{$v.IPAddress}} {{end}}' 2>/dev/null
done
echo "=== local docker images (redis/java/nginx) ==="
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' 2>/dev/null | grep -Ei 'redis|temurin|java|nginx|pause|busybox' | head -20
echo "=== redis-server binary in WSL ==="
command -v redis-server || echo "no redis-server"
echo "=== from k3d node: detailed gateway test ==="
docker exec k3d-v3-server-0 sh -c 'for hp in 172.18.0.1:3307 172.18.0.1:5432 172.18.0.1:9092; do h=${hp%%:*}; p=${hp##*:}; if timeout 2 nc -z "$h" "$p" 2>/dev/null; then echo "$hp nc-OK"; else echo "$hp nc-FAIL"; fi; done' 2>&1 | head -10
echo "=== from k3d node: curl gateway ==="
docker exec k3d-v3-server-0 sh -c 'curl -sS -m 3 -o /dev/null -w "%{http_code}\n" http://172.18.0.1:3307 2>&1' 2>&1 | head -3
echo "=== k3d node container networks ==="
docker inspect k3d-v3-server-0 --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} IP={{$v.IPAddress}}{{end}}' 2>/dev/null
