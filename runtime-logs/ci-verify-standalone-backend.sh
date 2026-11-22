#!/usr/bin/env bash

# @description 历史脚本 ci-verify-standalone-backend.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash ci-verify-standalone-backend.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 单机真实启动校验-backend：systemd 安装→启动→探活 /captchaImage=200

set -euo pipefail

WORK=/tmp/ci-verify

JAVA_BIN=/home/dev/.cache/ci-toolchain/jdk-17.0.21+9/bin/java

[ -x "$JAVA_BIN" ] || JAVA_BIN="$(readlink -f "$(command -v java)")"

DB_PW="$(cat "$WORK/mysql.pw")"

ITOKEN="$(docker exec k3d-v3-server-0 kubectl get secret car-monit-cluster-secrets -o jsonpath='{.data.internal-token}' | base64 -d)"

ESECRET="$(docker exec k3d-v3-server-0 kubectl get secret car-monit-cluster-secrets -o jsonpath='{.data.export-secret}' | base64 -d)"

echo "java=$JAVA_BIN itoken_len=${#ITOKEN} esec_len=${#ESECRET}"

sudo install -d /opt/car-monit-backend /etc/car-monit

sudo install -m 0644 "$WORK/car-monit-backend.jar" /opt/car-monit-backend/app.jar

sudo tee /etc/car-monit/backend.env >/dev/null <<EOF

SPRING_DATA_REDIS_HOST=172.18.0.1

SPRING_DATA_REDIS_PORT=6379

SPRING_DATASOURCE_DRUID_MASTER_PASSWORD=${DB_PW}

TRAFFIC_API_INTERNAL_TOKEN=${ITOKEN}

EXPORT_DOWNLOAD_SECRET=${ESECRET}

VEHICLE_MONITOR_BASE_URL=http://127.0.0.1:9902

LOG_ROOT_LEVEL=info

EOF

sudo chmod 600 /etc/car-monit/backend.env

sudo tee /etc/systemd/system/car-monit-backend.service >/dev/null <<EOF

[Unit]

Description=car-monit backend standalone (verify)

After=network-online.target



[Service]

Type=simple

User=root

WorkingDirectory=/opt/car-monit-backend

EnvironmentFile=/etc/car-monit/backend.env

ExecStart=${JAVA_BIN} -Xms128m -Xmx256m -XX:+UseSerialGC -jar /opt/car-monit-backend/app.jar --server.port=9989 --spring.datasource.driverClassName=com.mysql.cj.jdbc.Driver --spring.datasource.druid.master.url=jdbc:mysql://172.18.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=Asia/Shanghai&allowMultiQueries=true --logging.level.p6spy=OFF

Restart=always

RestartSec=5

LimitNOFILE=65535



[Install]

WantedBy=multi-user.target

EOF

sudo systemctl stop car-monit-backend 2>/dev/null || true

sudo systemctl daemon-reload

sudo systemctl enable car-monit-backend

sudo systemctl restart car-monit-backend

echo "=== health ==="

for i in $(seq 1 60); do

  c=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9989/captchaImage || true)

  if [ "$c" = "200" ]; then echo "STANDALONE_BACKEND_OK try=$i"; exit 0; fi

  sleep 2

done

echo "STANDALONE_BACKEND_FAIL"

sudo systemctl status car-monit-backend --no-pager | tail -10 || true

sudo journalctl -u car-monit-backend --no-pager | tail -30 || true

exit 1

