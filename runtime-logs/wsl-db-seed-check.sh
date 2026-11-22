#!/usr/bin/env bash
# @description 历史脚本 wsl-db-seed-check.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash wsl-db-seed-check.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION
# 文件：wsl-db-seed-check.sh
# 用途：检查 WSL Docker 中本地测试数据库的连通性和种子数据。
# 思路：只读查询 MySQL carmonitdb 与 openGauss 实例，确认本机服务复测可连接真实数据库。
# 风险：只读 SELECT / 列表查询，不修改数据；凭据仅用于本地容器。
echo "=== mysql carmonitdb ==="
docker exec mysql_wsl mysql -uroot -proot -D carmonitdb -e "select count(*) as sys_user from sys_user; select count(*) as car_info from car_info;" 2>&1 | head -20
echo "=== gauss containers ==="
docker ps --format '{{.Names}}' | grep -i -E 'gauss|postgres' || true
echo "=== gsql path ==="
docker exec -u omm opengauss sh -lc 'command -v gsql || find /usr/local -name gsql -type f 2>/dev/null | head -3' 2>&1 | head -10
echo "=== gauss databases ==="
docker exec -u omm opengauss sh -lc 'gsql -d postgres -c "\l"' 2>&1 | head -20 || true
