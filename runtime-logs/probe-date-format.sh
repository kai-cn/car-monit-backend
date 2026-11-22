#!/bin/sh
# LEGACY-SCRIPT-ANNOTATION
# 文件：probe-date-format.sh
# 用途：只读检查/诊断。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：通常只读；若脚本内有明确写操作以其自身说明为准。
cd "D:/work/IdeaProjects/car-monit-api" || exit 1
git filter-branch -f --env-filter '
  echo "PROBE CT=[$GIT_COMMITTER_DATE] AT=[$GIT_AUTHOR_DATE]" >&2
' -- master