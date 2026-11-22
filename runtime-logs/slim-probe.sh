#!/usr/bin/env bash

# @description 历史脚本 slim-probe.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash slim-probe.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

B=/home/dev/k3s-build

echo "=== image sizes ==="

docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -E 'car-monit|mysql:8.0.30|opengauss|k3s' | head -10

echo "=== jar sizes ==="

ls -lh "$B/api.jar" "$B/backend.jar" 2>/dev/null

echo "=== api.jar top nested libs (by uncompressed size) ==="

unzip -l "$B/api.jar" 2>/dev/null | grep 'BOOT-INF/lib/' | sort -k1,1nr | head -22

echo "=== backend.jar top nested libs ==="

unzip -l "$B/backend.jar" 2>/dev/null | grep 'BOOT-INF/lib/' | sort -k1,1nr | head -22

echo "=== jar composition ==="

for j in api backend; do

  echo "--- $j ---"

  unzip -l "$B/$j.jar" 2>/dev/null | awk '/BOOT-INF\/lib\// {lib+=$1} /BOOT-INF\/classes\// {cls+=$1} END {printf "libs=%.1fMB classes=%.1fMB\n", lib/1048576, cls/1048576}'

done

echo "=== DB container live memory ==="

docker stats --no-stream --format '{{.Name}} {{.MemUsage}} {{.MemPerc}}' mysql_wsl opengauss 2>/dev/null

echo "=== DB current limits ==="

for c in mysql_wsl opengauss; do docker inspect --format '{{.Name}} mem={{.HostConfig.Memory}} swap={{.HostConfig.MemorySwap}}' "$c" 2>/dev/null; done

echo "=== JDK dir size ==="

du -sh /home/dev/.cache/ci-toolchain/jdk-25.0.5+8 2>/dev/null

