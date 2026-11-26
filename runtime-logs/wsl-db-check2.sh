#!/usr/bin/env bash
# @description 历史脚本 wsl-db-check2.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash wsl-db-check2.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# 用途：只读检查 WSL Docker 中的 MySQL/openGauss 测试数据。
# 思路：通过容器内客户端查询关键表和实例状态，不修改任何数据。
# 风险：只读查询；使用本地测试凭据。
echo "MYSQL"
docker exec mysql_wsl mysql -uroot -proot -D carmonitdb -e 'select count(*) as sys_user from sys_user; select count(*) as car_info from car_info;' 2>&1 | head -20
echo "GAUSS"
docker ps --format '{{.Names}}' | grep -i gauss || true
docker exec -u omm opengauss sh -lc 'command -v gsql || find /usr/local -name gsql -type f 2>/dev/null | head -3' 2>&1 | head -5
echo "SUDO"
sudo -n true 2>&1 && echo SUDO_OK || echo SUDO_NEEDS_PASSWORD
