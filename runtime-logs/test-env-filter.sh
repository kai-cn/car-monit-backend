#!/bin/sh

# @description 历史脚本 test-env-filter.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash test-env-filter.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# LEGACY-SCRIPT-ANNOTATION

# 文件：test-env-filter.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

check() {

  GIT_COMMITTER_DATE="$1"

  GIT_AUTHOR_DATE="$2"

  . /d/work/runtime-logs/env-filter-cpp.sh

  echo "IN=$1|$2 => CT=$ct AT=$at NEWCD=$GIT_COMMITTER_DATE"

}

check "@1795319323 +0800" "@1794124711 +0800"

check "@1795319183 +0800" "@1794118000 +0800"

check "@1795320056 +0800" "@1795320056 +0800"

check "@1795280353 +0800" "@1795280353 +0800"

check "@1794900904 +0800" "@1794900904 +0800"