#!/usr/bin/env bash
# @description 查看 WSL master clone 的完整修改状态与关键 diff，供提交前复核。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 01:00:50
# @usage bash runtime-logs/wsl-final-review.sh
# @dependencies WSL master clones。
set -uo pipefail
for name in car-monit-backend car-monit-api; do
  repo=/home/dev/IdeaProjects/$name
  echo "=== $name ==="
  git -C "$repo" status --short
  git -C "$repo" diff --stat
  git -C "$repo" diff -- . ':!runtime-logs' | sed -n '1,260p'
done
