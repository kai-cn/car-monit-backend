#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== host: 172.18.0.1:6379 ping ==="
redis-cli -h 172.18.0.1 -p 6379 ping 2>&1
echo "=== redis-single bind/port/protected ==="
grep -E '^bind|^port|^protected-mode' /srv/redis/etc/redis-single.conf 2>&1
echo "=== pod: connect 172.18.0.1:6379 ==="
docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-backend -- bash -c 'timeout 3 bash -c "echo > /dev/tcp/172.18.0.1/6379" && echo POD_CAN_CONNECT || echo POD_CANNOT' 2>&1
echo "=== pod: connect 172.18.0.1:3307 (mysql, control) ==="
docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-backend -- bash -c 'timeout 3 bash -c "echo > /dev/tcp/172.18.0.1/3307" && echo POD_MYSQL_OK || echo POD_MYSQL_FAIL' 2>&1
