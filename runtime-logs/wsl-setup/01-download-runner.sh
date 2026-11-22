#!/usr/bin/env bash

# @description 历史脚本 01-download-runner.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash 01-download-runner.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# LEGACY-SCRIPT-ANNOTATION

# 文件：01-download-runner.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

set -uo pipefail

cd /opt/actions-runner || exit 1

URL='https://github.com/actions/runner/releases/download/v2.338.2/actions-runner-linux-x64-2.338.2.tar.gz'

echo "start $(date -Is)" > /opt/actions-runner/dl.log

if curl -fsSL --retry 3 --max-time 900 -o runner.tar.gz "$URL"; then

  echo "download ok $(du -h runner.tar.gz)" >> /opt/actions-runner/dl.log

  tar xzf runner.tar.gz

  ./bin/Runner.Listener --version > /opt/actions-runner/version.txt 2>&1 || true

  echo "extract done $(date -Is)" >> /opt/actions-runner/dl.log

  touch /opt/actions-runner/dl.done

else

  echo "download FAILED rc=$? $(date -Is)" >> /opt/actions-runner/dl.log

  touch /opt/actions-runner/dl.failed

fi

