#!/usr/bin/env bash
# @description 历史脚本 11-pull-k3s-image.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash 11-pull-k3s-image.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION
# 文件：11-pull-k3s-image.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set -u
LOG=/tmp/k3s-image.log
echo "start $(date -Is)" > "$LOG"
docker pull docker.1panel.live/rancher/k3s:v1.31.5-k3s1 >> "$LOG" 2>&1
echo "PULL_RC=$? $(date -Is)" >> "$LOG"
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' >> "$LOG" 2>&1
echo "done" >> "$LOG"
touch /tmp/k3s-image.done
