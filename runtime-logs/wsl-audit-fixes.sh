#!/usr/bin/env bash
# @description 审计 WSL master 中遗留表名、workflow token 与下游 baseUrl 配置，确认修复缺口。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 01:00:50
# @usage bash runtime-logs/wsl-audit-fixes.sh
# @dependencies WSL master clones。
set -uo pipefail
B=/home/dev/IdeaProjects/car-monit-backend
A=/home/dev/IdeaProjects/car-monit-api
echo "=== geometry_copy1 ==="
grep -R -n 'geometry_copy1' "$B" --include='*.go' --include='*.py' --include='*.rs' --include='*.xml' --include='*.cpp' --include='*.hpp' 2>/dev/null | head -30 || true
echo "=== workflow env ==="
grep -n 'TOKEN__SECRET\|VEHICLE_MONITOR_BASE_URL\|CARMONIT_TOKEN_SECRET\|APP_TOKEN' "$B/.github/workflows/crosslang-full-parity-cloud.yml" "$A/.github/workflows/crosslang-full-parity-cloud.yml" 2>/dev/null | head -40 || true
echo "=== selftest imports ==="
sed -n '1,12p' "$A/car-monit-api-go/internal/handler/selftest.go"
echo "=== git diff names ==="
git -C "$B" diff --name-only
git -C "$A" diff --name-only
