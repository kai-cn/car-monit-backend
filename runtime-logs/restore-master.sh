#!/bin/sh
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