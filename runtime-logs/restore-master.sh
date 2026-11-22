#!/bin/sh

# @description 历史脚本 restore-master.sh：恢复工作树、提交元数据或容器状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash restore-master.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# LEGACY-SCRIPT-ANNOTATION

# 文件：restore-master.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

cd "D:/work/IdeaProjects/car-monit-api" || exit 1

git update-ref refs/heads/master ce9a0f31417c99139560b511ddcc7cac9648e714

rm -rf .git-rewrite

echo "MASTER_NOW=$(git rev-parse master)"

echo "TREE_NOW=$(git rev-parse 'master^{tree}')"

echo "COUNT_NOW=$(git rev-list --count master)"