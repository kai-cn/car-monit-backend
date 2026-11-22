#!/bin/bash

# @description 历史脚本 test_rss2.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash test_rss2.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程；Java 运行时
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -uo pipefail

JAR=/mnt/d/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api-1.0.jar

JAVA=/home/dev/tools/mandrel-25/bin/java

GS_PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -1)

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL="jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&serverTimezone=Asia/Shanghai"

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$GS_PASS"

export EXPORT_DOWNLOAD_SECRET=x



sh -c "$JAVA -jar $JAR --server.port=19905" >/tmp/rssapp.log 2>&1 &

SH_PID=$!

for i in $(seq 1 90); do (echo > /dev/tcp/127.0.0.1/19905) 2>/dev/null && break; sleep 1; done

echo "shell pid=$SH_PID"

echo "=== shell-only VmRSS (old bug) ==="

grep VmRSS /proc/$SH_PID/status 2>/dev/null | tr -s ' '

echo "=== tree RSS via parity_probe._tree_rss_linux ==="

SH_PID=$SH_PID python3 -c "

import importlib.util, os

spec=importlib.util.spec_from_file_location('pp','/mnt/d/work/runtime-logs/parity_probe.py')

m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

print('tree_rss_mb =', m._tree_rss_linux(int(os.environ['SH_PID'])))

"

pkill -f "server.port=19905" 2>/dev/null; kill $SH_PID 2>/dev/null

