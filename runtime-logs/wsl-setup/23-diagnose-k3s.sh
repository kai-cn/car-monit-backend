#!/usr/bin/env bash

# @description 历史脚本 23-diagnose-k3s.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash 23-diagnose-k3s.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION

# 文件：23-diagnose-k3s.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1 k3d-v3-serverlb; do

  echo "==== $n ===="

  docker inspect "$n" | jq '.[0] | {RestartCount, Status: .State.Status, ExitCode: .State.ExitCode, OOM: .State.OOMKilled, Error: .State.Error, RestartPolicy: .HostConfig.RestartPolicy.Name}'

  docker logs "$n" --tail 5 2>&1 | tail -5

done

echo "==== MEM ===="

free -m | head -3

echo "==== OOM in dmesg ===="

dmesg 2>/dev/null | grep -i -E 'oom|killed process' | tail -8

