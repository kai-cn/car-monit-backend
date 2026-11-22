#!/bin/bash

# @description 历史脚本 test_rss.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash test_rss.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程；Java 运行时
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Verify tree-RSS sampling returns realistic values (~hundreds of MB) for java.

set -uo pipefail

PR=/mnt/d/work/runtime-logs

JAR=/mnt/d/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api-1.0.jar

JAVA=/home/dev/tools/mandrel-25/bin/java

GS_PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -1)

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL="jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&serverTimezone=Asia/Shanghai"

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$GS_PASS"

export EXPORT_DOWNLOAD_SECRET=x



echo '--- start java under shell (mimic probe) ---'

sh -c "$JAVA -jar $JAR --server.port=19905" >/tmp/rssapp.log 2>&1 &

SH_PID=$!

for i in $(seq 1 90); do (echo > /dev/tcp/127.0.0.1/19905) 2>/dev/null && break; sleep 1; done

echo "shell pid=$SH_PID"

echo "=== shell-only RSS (old buggy behaviour) ==="

grep VmRSS /proc/$SH_PID/status 2>/dev/null

echo "=== tree RSS via python function ==="

python3 - <<'PY'

import sys; sys.path.insert(0,'/mnt/d/work/runtime-logs')

import importlib.util

spec=importlib.util.spec_from_file_location('pp','/mnt/d/work/runtime-logs/parity_probe.py')

m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

import os

sh=int(open('/tmp/shpid').read()) if os.path.exists('/tmp/shpid') else None

print('sh pid from file:', sh)

PY

echo "=== direct ps tree ==="

ps -eo pid,ppid,rss,comm --sort=-rss | head -8

pkill -f "server.port=19905" 2>/dev/null; kill $SH_PID 2>/dev/null

