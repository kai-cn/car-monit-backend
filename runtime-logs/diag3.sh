#!/usr/bin/env bash
# @description 历史脚本 diag3.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash diag3.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
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
