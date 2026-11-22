#!/usr/bin/env bash
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
