#!/usr/bin/env bash
# @description 历史脚本 wsl-mysql-ip-check.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash wsl-mysql-ip-check.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程；Java 运行时
# Purpose: inspect MySQL container IP and host port binding for local retest.
# Idea: print container network address and probe both host port and container IP.
# Risk: read-only connectivity probes.
echo "=== ps ==="
docker ps --format '{{.Names}}|{{.Ports}}' | grep mysql || true
echo "=== inspect ip ==="
docker inspect mysql_wsl --format '{{.NetworkSettings.IPAddress}}' 2>&1
echo "=== listeners ==="
ss -ltnp 2>/dev/null | grep -E ':3307|:3306|:19903|:6379' || true
echo "=== host probe ==="
timeout 5 bash -c '</dev/tcp/127.0.0.1/3307' 2>&1 && echo HOST_OK || echo HOST_FAIL
IP=$(docker inspect mysql_wsl --format '{{.NetworkSettings.IPAddress}}' 2>/dev/null)
echo "=== container ip probe $IP ==="
if [ -n "$IP" ]; then timeout 5 bash -c "</dev/tcp/$IP/3306" 2>&1 && echo IP_OK || echo IP_FAIL; fi
echo "=== java ==="
ps -ef | grep -E 'java -jar' | grep -v grep | head -20 || true
