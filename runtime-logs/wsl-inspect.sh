#!/usr/bin/env bash
# @description 历史脚本 wsl-inspect.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash wsl-inspect.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Purpose: inspect WSL Docker and Java environment for local retest.
# Idea: keep quoting inside a shell script so Windows command wrappers do not alter it.
# Risk: read-only inspection; no container or file changes.
echo USER=$(whoami)
echo DOCKER=$(command -v docker || true)
echo "=== containers ==="
docker ps --format '{{.Names}}|{{.Image}}|{{.Ports}}' 2>&1 | head -20
echo "=== images ==="
docker images --format '{{.Repository}}:{{.Tag}}' 2>&1 | head -20
echo "=== java ==="
java -version 2>&1 | head -3
echo "=== jvm dirs ==="
find /usr/lib/jvm /opt -maxdepth 3 -type f -name java 2>/dev/null | head -20
echo "=== junit jar ==="
ls -l /mnt/d/work/runtime-logs/junit-platform-console-standalone.jar 2>&1
echo "=== ports ==="
ss -ltnp 2>/dev/null | grep -E ':3306|:3307|:5432|:6379|:19903' | head -20 || true
