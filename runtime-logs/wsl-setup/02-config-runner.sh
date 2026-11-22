#!/usr/bin/env bash

# @description 历史脚本 02-config-runner.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash 02-config-runner.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# LEGACY-SCRIPT-ANNOTATION

# 文件：02-config-runner.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

set -uo pipefail

cd /opt/actions-runner || exit 1

: "${RUNNER_TOK:?registration token missing}"

if ./config.sh --url https://github.com/kai-cn/car-monit-backend \

    --token "$RUNNER_TOK" \

    --name wsl-k3s \

    --labels wsl-k3s \

    --unattended \

    --work _work \

    --replace > /opt/actions-runner/config.log 2>&1; then

  echo "ok $(date -Is)" > /opt/actions-runner/config.done

else

  echo "failed $(date -Is)" > /opt/actions-runner/config.failed

fi

