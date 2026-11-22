#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
PW=$(cat /tmp/ci-verify/mysql.pw)
echo "=== host -> 172.18.0.1:3307 tcp ==="
timeout 4 bash -c 'echo > /dev/tcp/172.18.0.1/3307' && echo TCP_OK || echo TCP_FAIL
echo "=== mysql auth（用 Secret 里的 mysql-password）==="
docker exec mysql_wsl mysql -uroot -p"$PW" -e "select 1 as ok" 2>&1 | head -4
echo "=== 库列表 ==="
docker exec mysql_wsl mysql -uroot -p"$PW" -e "show databases" 2>&1 | head -12
echo "=== 后端 Deployment 的 DB 环境(脱敏) ==="
docker exec k3d-v3-server-0 kubectl get deploy car-monit-backend -o yaml 2>/dev/null | grep -A3 'SPRING_DATASOURCE_DRUID_MASTER_PASSWORD' | head -6
