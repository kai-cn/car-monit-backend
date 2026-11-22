#!/bin/sh
# LEGACY-SCRIPT-ANNOTATION
# 文件：clean-rewrite-dir.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
cd "D:/work/IdeaProjects/car-monit-api" || exit 1
rm -rf .git-rewrite
echo "REWRITE_DIR_EXISTS=$([ -d .git-rewrite ] && echo yes || echo no)"