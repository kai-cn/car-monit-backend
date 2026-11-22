#!/usr/bin/env bash

# @description 历史脚本 mem-now.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash mem-now.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do

  echo "--- $n ---"

  docker exec "$n" crictl stats -o json 2>/dev/null | jq -r '.stats[]? | select(.attributes.metadata.name | test("backend|api")) | [.attributes.metadata.name, (.memory.workingSetBytes.value // "null" | tostring), (.memory.usageBytes.value // "null" | tostring)] | @tsv' 2>/dev/null | head -6

done

