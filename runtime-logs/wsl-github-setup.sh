#!/usr/bin/env bash
# @description 检查并准备 WSL 内 GitHub HTTPS 克隆所需的 Git 凭据辅助配置。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 00:50:46
# @usage bash runtime-logs/wsl-github-setup.sh
# @dependencies git、gh、Windows 侧 git credential helper 或 GH_TOKEN。
set -uo pipefail
mkdir -p /home/dev/IdeaProjects
printf 'HOME=%s\n' "$HOME"
printf 'GIT=%s\n' "$(git --version 2>&1)"
printf 'GH=%s\n' "$(gh --version 2>&1 | head -1 || true)"
printf 'EXISTING=%s\n' "$(find /home/dev/IdeaProjects -maxdepth 1 -mindepth 1 -type d 2>/dev/null | tr '\n' ' ')"
printf 'CREDENTIAL_HELPER=%s\n' "$(git config --global --get credential.helper || true)"
printf 'TOKEN_ENV=%s\n' "$([ -n "${GH_TOKEN:-}" ] && echo set || echo unset)"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  printf 'GH_AUTH=ok\n'
else
  printf 'GH_AUTH=missing\n'
fi
curl -I -sS --max-time 15 https://github.com 2>&1 | head -3 || true
