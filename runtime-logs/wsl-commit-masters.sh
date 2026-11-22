#!/usr/bin/env bash
# @description 在 WSL backend/api master clone 中先本地提交再推送所有代码修复和文档证据。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 01:07:45
# @usage bash runtime-logs/wsl-commit-masters.sh
# @dependencies WSL master clones 与已配置的 GitHub 凭据。
set -euo pipefail
MSG='fix(parity): repair non-200 endpoints across Java/Python/Go/C++/Rust'

for name in car-monit-backend car-monit-api; do
  repo=/home/dev/IdeaProjects/$name
  echo "=== COMMIT $name ==="
  git -C "$repo" add -A -- .github scripts runtime-logs ruoyi-admin ruoyi-system ruoyi-quartz ruoyi-generator car-monit-py car-monit-go car-monit-rust car-monit-cpp car-monit-api-python car-monit-api-go car-monit-api-rust car-monit-api-cpp 2>/dev/null || true
  if git -C "$repo" diff --cached --quiet; then
    echo NOTHING_TO_COMMIT
  else
    git -C "$repo" commit -m "$MSG"
  fi
  git -C "$repo" push origin HEAD:master
  echo "HEAD $(git -C "$repo" rev-parse --short HEAD)"
done
