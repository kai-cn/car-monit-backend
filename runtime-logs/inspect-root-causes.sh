#!/usr/bin/env bash
# @description 检查代理环境、vehicleMonitor 配置、缺失表、BigScreen Bean 失败和生成器端点错误。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 07:38:02
# @usage bash runtime-logs/inspect-root-causes.sh
# @dependencies WSL master 与日志。
set -uo pipefail
B=/home/dev/IdeaProjects/car-monit-backend
L=/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream
echo '=== proxy env ==='
env | grep -iE '^(http|https|all|no)_proxy=' || true
echo '=== vehicleMonitor config ==='
grep -R -n 'baseUrl\|7890\|9902' "$B/ruoyi-admin/src/main/resources/application.yml" "$B/ruoyi-system/src/main/java/com/ruoyi/base/service/forest" 2>/dev/null | head -40
echo '=== sys_upgrade_info in DB ==='
docker exec mysql_wsl mysql -uroot -proot -D carmonitdb -e "show tables like 'sys_upgrade_info';" 2>&1 | tail -5
echo '=== bigScreen bean error ==='
grep -n -A 30 "Error creating bean with name 'bigScreenExportController'" "$L/app.log" 2>/dev/null | head -60
echo '=== generator errors ==='
grep -n -E "GenController|tool/gen" "$L/app.log" 2>/dev/null | tail -20
