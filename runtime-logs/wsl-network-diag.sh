#!/usr/bin/env bash
# @description 诊断 WSL 内 GitHub 443 不可达问题，检查 DNS、路由、代理与基本连通性。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 00:50:46
# @usage bash runtime-logs/wsl-network-diag.sh
# @dependencies iproute2、curl、resolv.conf。
set -uo pipefail
printf '=== resolv.conf ===\n'
cat /etc/resolv.conf 2>/dev/null || true
printf '=== ip route ===\n'
ip route 2>/dev/null || true
printf '=== proxy env ===\n'
env | grep -iE '^(http|https|all)_proxy=' || true
printf '=== windows proxy env ===\n'
powershell.exe -NoProfile -Command "[Environment]::GetEnvironmentVariable('HTTP_PROXY','User'); [Environment]::GetEnvironmentVariable('HTTPS_PROXY','User'); [Environment]::GetEnvironmentVariable('ALL_PROXY','User')" 2>/dev/null || true
printf '=== dns github ===\n'
getent hosts github.com || true
printf '=== curl 443 ===\n'
curl -4 -I -sS --max-time 10 https://github.com 2>&1 | head -5 || true
printf '=== curl http ===\n'
curl -4 -I -sS --max-time 10 http://github.com 2>&1 | head -5 || true
printf '=== host connectivity ===\n'
curl -4 -I -sS --max-time 10 https://www.baidu.com 2>&1 | head -3 || true
