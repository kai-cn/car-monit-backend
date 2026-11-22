#!/usr/bin/env bash
# @description 修复 WSL 内 GitHub hosts 解析并克隆 backend/api master 到 /home/dev/IdeaProjects。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 00:50:46
# @usage bash runtime-logs/wsl-fix-github-clone.sh
# @dependencies sudo、git、Windows 侧 git credential helper 或 GH_TOKEN。
set -uo pipefail
ROOT=/home/dev/IdeaProjects
mkdir -p "$ROOT"

# GitHub 在 WSL/Windows hosts 中被错误指向 127.0.0.1；使用公共 DNS 返回的真实地址。
for name in github.com api.github.com codeload.github.com; do
  sudo sed -i -E "/[[:space:]]${name//./\\.}$/d" /etc/hosts
done
sudo bash -c "printf '%s\n' '20.6.7.17 github.com' '20.6.7.17 api.github.com' '20.6.7.17 codeload.github.com' >> /etc/hosts"

# 凭据优先从 GH_TOKEN 提供；否则尝试 Windows git credential helper。
if [ -z "${GH_TOKEN:-}" ] && [ -f /home/dev/.gh_token_wsl ]; then
  GH_TOKEN=$(cat /home/dev/.gh_token_wsl)
fi
if [ -z "${GH_TOKEN:-}" ]; then
  echo NO_GITHUB_TOKEN
  exit 2
fi
export GH_TOKEN

for repo in car-monit-backend car-monit-api; do
  if [ -d "$ROOT/$repo/.git" ]; then
    echo "EXISTS $repo"
    git -C "$ROOT/$repo" remote set-url origin "https://x-access-token:${GH_TOKEN}@github.com/kai-cn/${repo}.git"
    git -C "$ROOT/$repo" fetch origin master
    git -C "$ROOT/$repo" checkout -B master origin/master
  else
    git clone --branch master --single-branch "https://x-access-token:${GH_TOKEN}@github.com/kai-cn/${repo}.git" "$ROOT/$repo" || exit 3
  fi
  echo "CLONED $repo $(git -C "$ROOT/$repo" rev-parse --short HEAD)"
done
