#!/usr/bin/env bash
# @description 检查 WSL master 工作树状态、最近提交与脱敏后的 remote URL。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 01:07:45
# @usage bash runtime-logs/wsl-status-masked.sh
# @dependencies WSL master clones。
set -uo pipefail
for name in car-monit-backend car-monit-api; do
  repo=/home/dev/IdeaProjects/$name
  echo "=== $name ==="
  git -C "$repo" rev-parse --short HEAD
  git -C "$repo" status --short | head -20
  git -C "$repo" log -3 --oneline
  url=$(git -C "$repo" remote get-url origin)
  echo "REMOTE ${url%%@*}@<redacted>"
done
