#!/usr/bin/env bash

# @description 历史脚本 16-push-backend.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash 16-push-backend.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# LEGACY-SCRIPT-ANNOTATION

# 文件：16-push-backend.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

set -u

: "${GIT_TOK:?token missing}"

LOG=/tmp/push-backend.log

cd /mnt/d/work/IdeaProjects/car-monit-backend-java-V3 || exit 1

for n in 1 2 3; do

  echo "attempt $n $(date -Is)" >> "$LOG"

  git -c credential.helper= -c "http.extraheader=AUTHORIZATION: bearer $GIT_TOK" \

    push origin car-monit-backend-java-V3 >> "$LOG" 2>&1

  rc=$?

  echo "RC=$rc" >> "$LOG"

  if [ "$rc" -eq 0 ]; then break; fi

  sleep 5

done

tail -8 "$LOG"

