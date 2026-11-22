#!/usr/bin/env bash
# @description 将 WSL /home/dev/IdeaProjects 下的 backend/api clone 同步到远端 master 最新提交。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 00:50:46
# @usage bash runtime-logs/wsl-sync-master.sh
# @dependencies git、已配置的 GitHub 凭据。
set -uo pipefail
for name in car-monit-backend car-monit-api; do
  repo=/home/dev/IdeaProjects/$name
  echo "=== $name ==="
  if [ ! -d "$repo/.git" ]; then
    echo MISSING
    continue
  fi
  git -C "$repo" fetch origin master || continue
  git -C "$repo" checkout -B master origin/master
  echo "HEAD $(git -C "$repo" rev-parse --short HEAD)"
  git -C "$repo" status --short | head -5
done
