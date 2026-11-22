#!/usr/bin/env bash

# @description 历史脚本 24-debug-runner.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash 24-debug-runner.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# LEGACY-SCRIPT-ANNOTATION

# 文件：24-debug-runner.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

systemctl stop actions-runner.service 2>/dev/null || true

pkill -9 -f '/opt/actions-runner/bin/Runner.Listener' 2>/dev/null || true

sleep 2

cd /opt/actions-runner

runuser -u dev -- timeout 20 ./run.sh > /tmp/runner-debug.log 2>&1

echo "RUN_RC=$?"

tail -20 /tmp/runner-debug.log

systemctl start actions-runner.service

