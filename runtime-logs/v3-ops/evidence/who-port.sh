#!/usr/bin/env bash

# @description 历史脚本 who-port.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash who-port.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# LEGACY-SCRIPT-ANNOTATION

# 文件：who-port.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

# Find who holds a TCP port using /proc (no lsof/ss needed), working around the

# fact that `ss` occasionally reports nothing for a socket that still binds-fails.

set -u

PORT=${1:-9902}

HEX=$(printf '%04X' "$PORT")



echo "port $PORT = 0x$HEX"

echo "=== /proc/net/tcp (state 0A=LISTEN) ==="

grep -i ":$HEX " /proc/net/tcp 2>/dev/null | head -n 5

echo "=== /proc/net/tcp6 ==="

grep -i ":$HEX " /proc/net/tcp6 2>/dev/null | head -n 5

echo "=== all procs with a socket inode on that port ==="

INODES=$(awk -v h=":$HEX" '$2 ~ h {print $10}' /proc/net/tcp /proc/net/tcp6 2>/dev/null | sort -u)

echo "inodes: ${INODES:-none}"

for ino in $INODES; do

  for fd in /proc/[0-9]*/fd/*; do

    if [ "$(readlink "$fd" 2>/dev/null)" = "socket:[$ino]" ]; then

      pid=${fd#/proc/}; pid=${pid%%/*}

      echo "  held by pid=$pid cmd=$(tr '\0' ' ' < /proc/$pid/cmdline | cut -c1-100)"

    fi

  done

done

