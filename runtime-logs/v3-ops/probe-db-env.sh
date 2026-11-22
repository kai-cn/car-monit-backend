#!/usr/bin/env bash

# @description 历史脚本 probe-db-env.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash probe-db-env.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Read-only probe: MySQL / openGauss container ports and credential variable NAMES.

# Never prints credential values.

echo '=== listening ports ==='

ss -lnt 2>/dev/null | grep -E ':(3307|5432|6379|9200|9092|19902|18080)\b' || true

echo '=== containers ==='

docker ps --format '{{.Names}} | {{.Status}} | {{.Ports}}' 2>/dev/null

echo '=== mysql env keys ==='

docker exec mysql_wsl env 2>/dev/null | sed -n 's/^\([^=]*\)=.*/\1/p' | grep -Ei 'mysql|pass|user' | head -20

echo '=== opengauss env keys ==='

docker exec opengauss env 2>/dev/null | sed -n 's/^\([^=]*\)=.*/\1/p' | grep -Ei 'gs_|pass|user' | head -20

echo '=== mysql connectivity (no auth) ==='

timeout 3 bash -c 'cat < /dev/null > /dev/tcp/127.0.0.1/3307' && echo MYSQL_3307_OPEN || echo MYSQL_3307_CLOSED

echo '=== jdbc URL reachability from WSL host ==='

timeout 3 bash -c 'cat < /dev/null > /dev/tcp/172.18.0.1/5432' && echo GS_5432_OPEN || echo GS_5432_CLOSED

