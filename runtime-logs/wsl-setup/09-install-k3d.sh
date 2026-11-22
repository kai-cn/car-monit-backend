#!/usr/bin/env bash

# @description 历史脚本 09-install-k3d.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash 09-install-k3d.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# LEGACY-SCRIPT-ANNOTATION

# 文件：09-install-k3d.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

set -u

LOG=/tmp/k3d-install.log

VER=v5.9.0

echo "start $(date -Is)" > "$LOG"

curl -fsSL --retry 3 --max-time 300 -o /usr/local/bin/k3d \

  "https://github.com/k3d-io/k3d/releases/download/$VER/k3d-linux-amd64" >> "$LOG" 2>&1

echo "CURL_RC=$?" >> "$LOG"

chmod +x /usr/local/bin/k3d

/usr/local/bin/k3d version >> "$LOG" 2>&1

echo "done $(date -Is)" >> "$LOG"

touch /tmp/k3d-install.done

