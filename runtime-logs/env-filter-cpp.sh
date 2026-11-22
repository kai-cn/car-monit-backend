#!/bin/sh
# LEGACY-SCRIPT-ANNOTATION
# 文件：env-filter-cpp.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
ct=$(printf '%s' "$GIT_COMMITTER_DATE" | sed 's/^@//' | cut -d' ' -f1)
at=$(printf '%s' "$GIT_AUTHOR_DATE" | sed 's/^@//' | cut -d' ' -f1)
if [ "$ct" -ge 1795319180 ] && [ "$ct" -le 1795319330 ] && [ "$at" -lt 1795200000 ]; then
  export GIT_COMMITTER_DATE="$GIT_AUTHOR_DATE"
fi