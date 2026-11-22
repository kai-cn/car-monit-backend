#!/usr/bin/env bash

# @description 历史脚本 probe4.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash probe4.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -u

echo "=== gateway reachability via wget (k3d server node) ==="

for hp in 172.18.0.1:3307 172.18.0.1:5432 172.17.0.3:3306 172.17.0.2:5432; do

  out=$(docker exec k3d-v3-server-0 wget -S --spider -T 2 "http://$hp/" 2>&1 | head -3 | tr '\n' ' ')

  echo "$hp => $out"

done

echo "=== Linux JDK 17 ==="

ls -la /home/dev/.cache/ci-toolchain/jdk-17.0.21+9/bin/java 2>/dev/null

/home/dev/.cache/ci-toolchain/jdk-17.0.21+9/bin/java -version 2>&1 | head -3

echo "=== redis-server deps ==="

ldd /usr/bin/redis-server 2>&1 | head -12

echo "=== candidate base image libc ==="

for img in ghcr.io/k3d-io/k3d-tools:5.9.0 rancher/k3s:v1.35.5-k3s1 mysql:8.0.30; do

  echo -n "$img: "; docker run --rm --entrypoint sh "$img" -c 'ldd --version 2>&1 | head -1' 2>&1 | head -1

done

echo "=== disk ==="

df -h / /mnt/d 2>/dev/null | head -5

