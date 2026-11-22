#!/usr/bin/env bash
# @description 历史脚本 probe-r9-detail.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash probe-r9-detail.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo '=== maven process state ==='
ps -o pid,ppid,stat,wchan:30,etime,args -p 12880 | cut -c1-180
echo '=== children of maven ==='
ps --ppid 12880 -o pid,stat,etime,comm,args | cut -c1-180
echo '=== children of build script ==='
ps --ppid 12012 -o pid,stat,etime,comm,args | cut -c1-180
echo '=== last 12 lines of r9 log ==='
tail -n 12 /mnt/d/work/runtime-logs/v3-ops/evidence/native-api-boot3-jdk21-linux-r9.log
