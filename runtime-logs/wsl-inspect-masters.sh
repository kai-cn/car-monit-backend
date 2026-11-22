#!/usr/bin/env bash
# @description 检查 WSL master clone 的目录结构、runtime-logs 与可用证据。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 00:50:46
# @usage bash runtime-logs/wsl-inspect-masters.sh
# @dependencies WSL 中已 clone 的 backend/api master。
set -uo pipefail
for name in car-monit-backend car-monit-api; do
  repo=/home/dev/IdeaProjects/$name
  echo "=== $name $(git -C "$repo" rev-parse --short HEAD) ==="
  ls -d "$repo"/* 2>/dev/null | head -30
  echo "--- runtime-logs ---"
  find "$repo/runtime-logs" -maxdepth 2 -type f 2>/dev/null | head -20
done
