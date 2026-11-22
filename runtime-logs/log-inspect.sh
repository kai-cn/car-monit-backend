#!/usr/bin/env bash
# @description 历史脚本 log-inspect.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash log-inspect.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== backend non-ERROR log samples ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=200 2>/dev/null | grep -E 'INFO|DEBUG|TRACE|Consume Time|Execute SQL' | head -12
echo "=== backend log level distribution ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=200 2>/dev/null | grep -oE ' (INFO|DEBUG|TRACE|WARN|ERROR) ' | sort | uniq -c
echo "=== first 12 lines ==="
docker exec k3d-v3-server-0 kubectl logs deploy/car-monit-backend --tail=200 2>/dev/null | head -12
