#!/bin/sh

# @description 历史脚本 probe-date-format.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash probe-date-format.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# LEGACY-SCRIPT-ANNOTATION

# 文件：probe-date-format.sh

# 用途：只读检查/诊断。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：通常只读；若脚本内有明确写操作以其自身说明为准。

cd "D:/work/IdeaProjects/car-monit-api" || exit 1

git filter-branch -f --env-filter '

  echo "PROBE CT=[$GIT_COMMITTER_DATE] AT=[$GIT_AUTHOR_DATE]" >&2

' -- master