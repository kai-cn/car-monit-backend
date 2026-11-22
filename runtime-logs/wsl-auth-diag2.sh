#!/usr/bin/env bash
# @description 诊断本机鉴权复测失败原因，读取应用日志与数据库连通性。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash runtime-logs/wsl-auth-diag2.sh
# @dependencies WSL、docker、grep、redis-cli/mysql 客户端。
echo "=== app log tail ==="
tail -60 /home/dev/local-auth-retest/app.log 2>/dev/null || true
echo "=== app errors ==="
grep -n -E 'ERROR|Exception|Druid|Connection|login|Login|认证|密码' /home/dev/local-auth-retest/app.log 2>/dev/null | tail -50 || true
echo "=== redis ping ==="
redis-cli -h 127.0.0.1 -p 6379 ping 2>&1 || true
echo "=== mysql ping ==="
mysql -h127.0.0.1 -P3307 -uroot -proot -e 'select 1' 2>&1 | head -5 || true
echo "=== containers ==="
docker ps --format '{{.Names}}|{{.Ports}}' 2>&1 | head -20
echo "=== processes ==="
ps -ef | grep -E 'java -jar|redis-server' | grep -v grep | head -20 || true
