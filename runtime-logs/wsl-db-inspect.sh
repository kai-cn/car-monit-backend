#!/usr/bin/env bash
# @description 历史脚本 wsl-db-inspect.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash wsl-db-inspect.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Purpose: inspect local WSL database container env and connectivity.
# Idea: keep all shell quoting inside a script file to avoid Windows wrapper issues.
# Risk: read-only except for SELECT 1 / ping probes.
echo "=== mysql env ==="
docker inspect mysql_wsl --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E 'MYSQL_ROOT|MYSQL_DATABASE|MYSQL_USER' || true
echo "=== opengauss env ==="
docker inspect opengauss --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E 'PASSWORD|USER|DB' || true
echo "=== mysql probe ==="
docker exec mysql_wsl mysql -uroot -proot -e 'select version(); show databases;' 2>&1 | head -20 || true
echo "=== opengauss probe ==="
docker exec -u omm opengauss gsql -d postgres -c 'select version();' 2>&1 | head -10 || true
echo "=== redis image ==="
docker image inspect redis:7-alpine --format '{{.Id}}' 2>&1 | head -2 || true
