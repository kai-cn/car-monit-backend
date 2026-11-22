#!/bin/sh
# LEGACY-SCRIPT-ANNOTATION
# 文件：fix-cpp-dates.sh
# 用途：本地或远端修复/改造。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：会修改文件、索引或远端，执行前确认可回滚。
cd "D:/work/IdeaProjects/car-monit-api" || exit 1
export FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch -f --env-filter '
  . /d/work/runtime-logs/env-filter-cpp.sh
' -- master > /d/work/runtime-logs/fix-cpp-dates.out 2>&1
echo FILTER_EXIT=$?