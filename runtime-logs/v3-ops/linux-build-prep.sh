#!/usr/bin/env bash

# @description 历史脚本 linux-build-prep.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash linux-build-prep.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Prepare WSL for the Linux native-image build (temporary 12GB/6cpu quota).

set -u

echo "==== linux native build prep ===="

echo "date      : $(date -Is)"

echo "cpu       : nproc=$(nproc)"

free -m | head -2

echo "---- stop non-essential containers (free RAM for native-image) ----"

for c in kafka-wsl es-wsl mysql_wsl opengauss; do

  if docker ps --format '{{.Names}}' | grep -qx "$c"; then

    docker stop "$c" >/dev/null 2>&1 && echo "stopped $c"

  else

    echo "not running: $c"

  fi

done

echo "---- remaining containers ----"

docker ps --format '{{.Names}} {{.Status}}'

echo "---- disk ----"

df -h / | tail -1

echo "---- toolchain ----"

/home/dev/tools/mandrel-25/bin/java -version 2>&1 | head -3

/home/dev/tools/mandrel-25/bin/native-image --version 2>&1 | head -3

for c in gcc g++ ld; do printf '%-6s %s\n' "$c" "$(command -v "$c" || echo MISSING)"; done

echo "PREP_OK"

