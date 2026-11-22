#!/usr/bin/env bash

# @description 历史脚本 ci-db-test.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash ci-db-test.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
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

