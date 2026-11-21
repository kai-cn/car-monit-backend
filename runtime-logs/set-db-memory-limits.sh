#!/usr/bin/env bash
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
