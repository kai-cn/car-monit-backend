#!/usr/bin/env bash
# @description 修复 WSL 内 GitHub 无法拉取/推送的问题：DNS 被污染为 127.0.0.1 时，
#              把经过实测的 GitHub IP 固化到 /etc/hosts，并配置本地 credential helper
#              让 HTTPS git 自动使用 gh_cred.py 缓存的 token（不弹窗、不回显）。
# @author Tencent Hunyuan Hy
# @date 2026-11-28 16:32:00
# @usage sudo bash runtime-logs/fix-github-connectivity-wsl.sh
# @dependencies sudo；仓库内 runtime-logs/gh_cred.py 与 git-credential-ghcached-wsl.py
# @sideEffect 修改 /etc/hosts（先备份）与全局 git credential 配置；不会输出 token。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="!python3 ${REPO_ROOT}/runtime-logs/git-credential-ghcached-wsl.py"
# 140.82.112.6 只服务 api.github.com（git smart HTTP 超时）；112.3 同时支持 git/api/codeload。
IP="140.82.112.3"

echo "[1/3] 固化 GitHub IP 到 /etc/hosts"
cp /etc/hosts "/etc/hosts.bak-git-fix-$(date +%Y%m%d%H%M%S)"
if ! grep -q "^${IP} github.com" /etc/hosts; then
  {
    echo ""
    echo "# GitHub 直连 IP（WSL DNS 污染修复，2026-11-28）"
    echo "${IP} github.com"
    echo "${IP} api.github.com"
    echo "${IP} codeload.github.com"
    echo "${IP} www.github.com"
  } >> /etc/hosts
fi
getent hosts github.com api.github.com

echo "[2/3] 配置 git credential helper"
git config --global --unset-all 'credential.https://github.com.helper' 2>/dev/null || true
git config --global --add 'credential.https://github.com.helper' ''
git config --global --add 'credential.https://github.com.helper' "$HELPER"

echo "[3/3] 验证"
printf 'protocol=https\nhost=github.com\nusername=kai-cn\n\n' | git credential fill \
  | sed 's/^password=.*/password=<redacted>/'
curl -sS --max-time 20 -o /dev/null -w 'git-smart HTTP=%{http_code}\n' \
  'https://github.com/kai-cn/car-monit-backend.git/info/refs?service=git-upload-pack'

echo "[done] 现在可执行 git fetch / git push origin master"
