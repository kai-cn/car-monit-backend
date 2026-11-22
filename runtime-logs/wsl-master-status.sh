#!/usr/bin/env bash
# @description 查看 WSL master clone 的修改文件与差异统计。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 01:00:50
# @usage bash runtime-logs/wsl-master-status.sh
# @dependencies WSL master clones。
set -uo pipefail
for name in car-monit-backend car-monit-api; do
  repo=/home/dev/IdeaProjects/$name
  echo "=== $name $(git -C "$repo" rev-parse --short HEAD) ==="
  git -C "$repo" status --short
  git -C "$repo" diff --stat
done
