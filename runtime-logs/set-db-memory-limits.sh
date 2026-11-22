#!/usr/bin/env bash
# @description 历史脚本 set-db-memory-limits.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash set-db-memory-limits.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Write GitHub Secrets or local configuration from runtime-supplied values only.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 实测上限（2026-11-14）：mysql_wsl 峰值 32.02MiB、opengauss 峰值 81.02MiB。
# 取峰值 + 96MiB 余量并设下限 256MiB，硬上限不超过 500m。
# 注意：docker update 只对运行中的容器生效；容器重建时必须带 --memory=256m --memory-swap=256m。
set -euo pipefail
MYSQL_LIMIT=${MYSQL_LIMIT:-256m}
OPENGAUSS_LIMIT=${OPENGAUSS_LIMIT:-256m}
docker update --memory="$MYSQL_LIMIT" --memory-swap="$MYSQL_LIMIT" mysql_wsl
docker update --memory="$OPENGAUSS_LIMIT" --memory-swap="$OPENGAUSS_LIMIT" opengauss
for c in mysql_wsl opengauss; do
  docker inspect --format '{{.Name}} mem={{.HostConfig.Memory}} swap={{.HostConfig.MemorySwap}} oom={{.State.OOMKilled}}' "$c"
done
