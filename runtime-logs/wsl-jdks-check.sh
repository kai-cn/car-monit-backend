#!/usr/bin/env bash
# @description 历史脚本 wsl-jdks-check.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash wsl-jdks-check.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Purpose: verify local JDKs can compile before repackaging.
# Idea: print java/javac versions from each toolchain used by the Java branch matrix.
# Risk: read-only version checks.
for d in \
  /usr/lib/jvm/java-1.8.0-openjdk-1.8.0.502.b07-1.oe2403sp4.x86_64 \
  /home/dev/tools/mandrel-java17-23.0.6.0-Final \
  /home/dev/tools/mandrel-java21-23.1.13.0-Final \
  /home/dev/tools/mandrel-java25-25.0.4.1-Final; do
  echo "=== $d ==="
  if [ -x "$d/bin/javac" ]; then "$d/bin/javac" -version 2>&1 | head -2; else echo NO_JAVAC; fi
  if [ -x "$d/bin/java" ]; then "$d/bin/java" -version 2>&1 | head -2; else echo NO_JAVA; fi
done
