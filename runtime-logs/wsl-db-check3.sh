#!/usr/bin/env bash
# @description 历史脚本 wsl-db-check3.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash wsl-db-check3.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Purpose: read-only check of local WSL Docker databases.
# Idea: query MySQL and openGauss container state before local service retest.
# Risk: SELECT only; no data changes.
echo MYSQL
docker exec mysql_wsl mysql -uroot -proot -D carmonitdb -e 'select count(*) as sys_user from sys_user; select count(*) as car_info from car_info;' 2>&1 | head -20
echo GAUSS
docker ps --format '{{.Names}}' | grep -i gauss || true
echo SUDO
sudo -n true 2>&1 && echo SUDO_OK || echo SUDO_NEEDS_PASSWORD
