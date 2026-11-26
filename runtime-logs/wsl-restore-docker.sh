#!/usr/bin/env bash
# @description 历史脚本 wsl-restore-docker.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash wsl-restore-docker.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Purpose: restore WSL Docker containers after WSL restart and clean stale local test processes.
# Idea: start mysql_wsl/redis_wsl if stopped, wait for ports, kill leftover java processes.
# Risk: starts local test containers and kills only local java test processes.
echo "=== kill stale java ==="
sudo pkill -9 -f 'ruoyi-admin.jar' 2>/dev/null || true
sudo pkill -9 -f 'junit-platform-console-standalone.jar' 2>/dev/null || true
sleep 2
echo "=== start containers ==="
docker start mysql_wsl 2>&1 || true
docker start redis_wsl 2>&1 || true
for i in $(seq 1 60); do
  M=0; R=0
  docker exec mysql_wsl mysql -uroot -proot -e 'select 1' >/dev/null 2>&1 && M=1
  docker exec redis_wsl redis-cli ping >/dev/null 2>&1 && R=1
  [ "$M" = 1 ] && [ "$R" = 1 ] && break
  sleep 2
done
echo "=== ps ==="
docker ps --format '{{.Names}}|{{.Ports}}'
echo "=== host ports ==="
ss -ltnp 2>/dev/null | grep -E ':3307|:6379|:19903' || true
echo "=== mysql data ==="
docker exec mysql_wsl mysql -uroot -proot -D carmonitdb -e 'select count(*) from sys_user; select count(*) from car_info;' 2>&1 | head -10
