#!/bin/sh
# @description 历史脚本 clean-rewrite-dir.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash clean-rewrite-dir.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# LEGACY-SCRIPT-ANNOTATION
# 文件：clean-rewrite-dir.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
cd "D:/work/IdeaProjects/car-monit-api" || exit 1
if [ -d .git-rewrite ]; then
  find .git-rewrite -type f -delete
  find .git-rewrite -depth -type d -empty -delete
fi
echo "REWRITE_DIR_EXISTS=$([ -d .git-rewrite ] && echo yes || echo no)"