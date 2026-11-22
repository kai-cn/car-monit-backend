#!/usr/bin/env bash
# @description 历史脚本 wsl-app-log-check.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash wsl-app-log-check.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Java 运行时
# Purpose: inspect local service startup failure details.
# Idea: print JDBC URL lines and the first connection exception from app.log.
# Risk: read-only.
echo "=== jdbc lines ==="
grep -E 'jdbc:|url:|Connection refused|Communications link|Access denied|Unknown database' /home/dev/local-retest/app.log 2>/dev/null | head -30 || true
echo "=== causes ==="
grep -E 'Caused by|APPLICATION FAILED|Error creating bean' /home/dev/local-retest/app.log 2>/dev/null | head -30 || true
echo "=== listeners ==="
ss -ltnp 2>/dev/null | grep -E ':19903|:3307|:3306|:6379' || true
echo "=== java processes ==="
ps -ef | grep -E 'ruoyi-admin.jar|java -jar' | grep -v grep | head -20 || true
