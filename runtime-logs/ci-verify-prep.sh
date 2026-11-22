#!/usr/bin/env bash

# @description 历史脚本 ci-verify-prep.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash ci-verify-prep.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 真实启动校验-准备：抽 jar、取 DB 口令(临时文件)、补字体

set -euo pipefail

WORK=/tmp/ci-verify

mkdir -p "$WORK"

echo "=== 抽 jar（从运行中的 slim 镜像）==="

docker run --rm --entrypoint cat car-monit-backend:slim /app/app.jar > "$WORK/car-monit-backend.jar"

docker run --rm --entrypoint cat car-monit-api:slim /app/app.jar > "$WORK/car-monit-api.jar"

ls -lh "$WORK"/car-monit-*.jar

echo "=== 取 DB 口令（写 600 临时文件，仅计数不回显）==="

docker exec k3d-v3-server-0 kubectl get secret car-monit-cluster-secrets -o jsonpath='{.data.mysql-password}' | base64 -d > "$WORK/mysql.pw"

docker exec k3d-v3-server-0 kubectl get secret car-monit-cluster-secrets -o jsonpath='{.data.opengauss-password}' | base64 -d > "$WORK/opengauss.pw"

chmod 600 "$WORK"/*.pw

echo "mysql_pw_len=$(wc -c < "$WORK/mysql.pw") opengauss_pw_len=$(wc -c < "$WORK/opengauss.pw")"

echo "=== 宿主字体 / java ==="

command -v java && java -version 2>&1 | head -1 || echo "NO java"

if ! fc-list >/dev/null 2>&1; then

  echo ">> 安装 fontconfig + dejavu 字体"

  sudo dnf install -y fontconfig dejavu-sans-fonts >/dev/null 2>&1 || true

fi

fc-list 2>/dev/null | head -2 || echo "still NO fc-list"

echo "=== jar 主类/版本 ==="

for j in "$WORK"/car-monit-*.jar; do

  echo "-- $j"; unzip -p "$j" META-INF/MANIFEST.MF 2>/dev/null | grep -iE 'Spring-Boot-Version|Main-Class|Build-Jdk' | head -3

done

