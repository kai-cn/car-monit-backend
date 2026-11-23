#!/usr/bin/env bash
# @description 校验 WSL Git 网络桥接可执行 fetch 与 push。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 05:10:00
# @usage bash runtime-logs/wsl-git-bridge-test.sh
# @dependencies /home/dev/local-bin/wsl-git、Windows git 凭据栈。
set -euo pipefail
for d in /home/dev/IdeaProjects/car-monit-backend /home/dev/IdeaProjects/car-monit-api; do
  echo "=== $d ==="
  /home/dev/local-bin/wsl-git -C "$d" fetch origin master
  /home/dev/local-bin/wsl-git -C "$d" ls-remote --heads origin master
done
