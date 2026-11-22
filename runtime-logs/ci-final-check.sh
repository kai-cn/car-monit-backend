#!/usr/bin/env bash

# @description 历史脚本 ci-final-check.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash ci-final-check.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

SVR_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' k3d-v3-server-0)

echo "=== 单机（systemd）==="

echo -n "standalone backend :9989/captchaImage = "; curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9989/captchaImage

echo -n "standalone api     :9902/base/section/list = "; curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9902/base/section/list

echo "=== 集群（NodePort, server=${SVR_IP}）==="

echo -n "cluster backend    :30989/captchaImage = "; curl -s -o /dev/null -w '%{http_code}\n' "http://${SVR_IP}:30989/captchaImage"

echo -n "cluster api        :30902/base/section/list = "; curl -s -o /dev/null -w '%{http_code}\n' "http://${SVR_IP}:30902/base/section/list"

echo "=== 集群 Pod ==="

docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' --no-headers 2>&1

echo "=== systemd ==="

systemctl is-active car-monit-backend car-monit-api

