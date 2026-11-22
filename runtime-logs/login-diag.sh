#!/usr/bin/env bash

# @description 历史脚本 login-diag.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash login-diag.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

echo "=== full login error ==="

curl -s -m 20 -X POST -H 'Content-Type: application/json' \

  -d '{"username":"admin","password":"${CARMONIT_ADMIN_PASSWORD}","code":"1234","uuid":"dummy"}' \

  http://172.18.0.2:30989/login

echo

echo "=== captcha config key in MySQL ==="

docker exec mysql_wsl mysql -uroot -proot -h127.0.0.1 -P3306 --batch --skip-column-names \

  -e "select config_key,config_value from carmonitdb.sys_config where config_key like '%captcha%';" 2>/dev/null || true

echo "=== code refs ==="

grep -rn 'selectCaptchaEnabled\|captchaEnabled' /mnt/d/work/IdeaProjects/car-monit-backend-jdk17/ruoyi-system/src/main/java /mnt/d/work/IdeaProjects/car-monit-backend-jdk17/ruoyi-framework/src/main/java 2>/dev/null | head -10

