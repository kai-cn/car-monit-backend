#!/usr/bin/env bash

# @description 历史脚本 ci-health.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash ci-health.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

SVR_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' k3d-v3-server-0)

LB_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' k3d-v3-serverlb)

echo "server=$SVR_IP lb=$LB_IP"

echo -n "backend captcha via server: "; curl -s -o /dev/null -w '%{http_code}\n' "http://${SVR_IP}:30989/captchaImage"

echo -n "backend captcha via lb:     "; curl -s -o /dev/null -w '%{http_code}\n' "http://${LB_IP}:30989/captchaImage"

echo -n "api list via server:        "; curl -s -o /dev/null -w '%{http_code}\n' "http://${SVR_IP}:30902/base/section/list"

echo -n "api list via lb:            "; curl -s -o /dev/null -w '%{http_code}\n' "http://${LB_IP}:30902/base/section/list"

