#!/usr/bin/env bash

# @description 历史脚本 ci-verify-standalone-api.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash ci-verify-standalone-api.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 单机真实启动校验-api：systemd 安装→启动→探活 /base/section/list=200

set -euo pipefail

WORK=/tmp/ci-verify

JAVA_BIN=/home/dev/.cache/ci-toolchain/jdk-17.0.21+9/bin/java

[ -x "$JAVA_BIN" ] || JAVA_BIN="$(readlink -f "$(command -v java)")"

OPW="$(cat "$WORK/opengauss.pw")"

ITOKEN="$(docker exec k3d-v3-server-0 kubectl get secret car-monit-cluster-secrets -o jsonpath='{.data.internal-token}' | base64 -d)"

echo "java=$JAVA_BIN opw_len=${#OPW} itoken_len=${#ITOKEN}"

sudo install -d /opt/car-monit-api /etc/car-monit

sudo install -m 0644 "$WORK/car-monit-api.jar" /opt/car-monit-api/app.jar

sudo tee /etc/car-monit/api.env >/dev/null <<EOF

SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD=${OPW}

TRAFFIC_INTERNAL_TOKEN=${ITOKEN}

SPRING_DATA_REDIS_HOST=172.18.0.1

SPRING_DATA_REDIS_PORT=6379

SPRING_KAFKA_BOOTSTRAP_SERVERS=172.18.0.1:9092

ELASTICSEARCH_HOST=172.18.0.1

ELASTICSEARCH_PORT=9200

ELASTICSEARCH_SCHEME=http

LOG_ROOT_LEVEL=info

EOF

sudo chmod 600 /etc/car-monit/api.env

sudo tee /etc/systemd/system/car-monit-api.service >/dev/null <<EOF

[Unit]

Description=car-monit api standalone (verify)

After=network-online.target



[Service]

Type=simple

User=root

WorkingDirectory=/opt/car-monit-api

EnvironmentFile=/etc/car-monit/api.env

ExecStart=${JAVA_BIN} --add-opens=java.base/java.lang=ALL-UNNAMED -Xms128m -Xmx256m -XX:+UseSerialGC -jar /opt/car-monit-api/app.jar --server.port=9902 --spring.datasource.dynamic.datasource.master.url=jdbc:postgresql://172.18.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&tinyInt1isBit=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai --traffic.query.engine=es --traffic.sync.enabled=true --spring.main.lazy-initialization=false --logging.level.p6spy=OFF

Restart=always

RestartSec=5

LimitNOFILE=65535



[Install]

WantedBy=multi-user.target

EOF

sudo systemctl stop car-monit-api 2>/dev/null || true

sudo systemctl daemon-reload

sudo systemctl enable car-monit-api

sudo systemctl restart car-monit-api

echo "=== health ==="

for i in $(seq 1 90); do

  c=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9902/base/section/list || true)

  if [ "$c" = "200" ]; then echo "STANDALONE_API_OK try=$i"; exit 0; fi

  sleep 2

done

echo "STANDALONE_API_FAIL"

sudo systemctl status car-monit-api --no-pager | tail -8 || true

sudo journalctl -u car-monit-api --no-pager | tail -30 || true

exit 1

