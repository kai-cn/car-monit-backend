#!/usr/bin/env bash
# @description 检查 geometry 与 geometry_copy1 表是否存在，并查看数据量，验证 syncAllGeometry 失败根因。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:33:26
# @usage bash runtime-logs/check-geometry-tables.sh
# @dependencies 本机 MySQL 容器 mysql_wsl。
docker exec mysql_wsl mysql -uroot -proot -D carmonitdb -e "show tables like 'geometry%'; select count(*) from geometry;" 2>&1
