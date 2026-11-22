#!/usr/bin/env bash

# @description 历史脚本 probe-mandrel.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash probe-mandrel.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -uo pipefail

echo "==== 7z / archive tools in WSL ===="

for c in 7z 7za 7zr p7zip bsdtar unzip; do printf '%-10s %s\n' "$c" "$(command -v "$c" 2>/dev/null || echo MISSING)"; done

echo "-- rpm --"; rpm -qa 2>/dev/null | grep -iE 'p7zip|7zip|libarchive' | head -10

echo "-- python py7zr --"; python3 -c "import py7zr; print('py7zr available', py7zr.__version__)" 2>&1 | head -3

echo "==== archive listing ===="

A=/mnt/d/jdk/mandrel-25.0.4.1-Final.7z

ls -l "$A"

if command -v 7z >/dev/null 2>&1; then 7z l "$A" 2>&1 | head -70; fi

echo "==== listening ports / processes ===="

ss -ltnp 2>/dev/null | grep -E ':(9989|9902|6379|6380|30989|30902|3307|5432|9200|9092)' || echo none

echo "-- java processes --"

ps -eo pid,rss,args --sort=-rss 2>/dev/null | grep -E '[j]ava|[r]uoyi|[p]ro-business' | head -20

echo "==== disk (root) ===="

sudo du -sh /var/lib/docker /var/lib/docker/overlay2 /var/lib/docker/volumes /var/lib/docker/containers 2>&1 | head -10

echo "-- biggest overlay2 --"; sudo du -sh /var/lib/docker/overlay2/* 2>/dev/null | sort -rh | head -12

echo "-- biggest volumes --"; sudo du -sh /var/lib/docker/volumes/* 2>/dev/null | sort -rh | head -12

echo "==== CI runner dirs ===="

ls -la /home/dev/ 2>/dev/null | head -20

echo "==== END ===="

