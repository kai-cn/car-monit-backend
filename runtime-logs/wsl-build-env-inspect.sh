#!/usr/bin/env bash
# @description 历史脚本 wsl-build-env-inspect.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash wsl-build-env-inspect.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Purpose: inspect WSL Java/Maven toolchains and mounted Java worktrees for local repackaging.
# Idea: list installed JVMs, Maven version/cache, and candidate worktrees without modifying files.
# Risk: read-only inspection; no source or dependency changes.
echo "=== java runtime ==="
java -version 2>&1 | head -3
echo "=== maven ==="
mvn -version 2>&1 | head -3
echo "=== jvm directories ==="
find /usr/lib/jvm /opt /home/dev -maxdepth 4 -type f -name java 2>/dev/null | head -30
echo "=== maven local repo ==="
du -sh /home/dev/.m2/repository 2>/dev/null || true
echo "=== worktrees ==="
for d in /mnt/d/work/IdeaProjects/car-monit-backend-new /mnt/d/work/IdeaProjects/car-monit-api /mnt/d/work/IdeaProjects/car-monit-backend-java-V3 /mnt/d/work/IdeaProjects/car-monit-api-java-V3 /mnt/d/work/IdeaProjects/car-monit-backend-jdk17 /mnt/d/work/IdeaProjects/car-monit-backend-jdk21 /mnt/d/work/IdeaProjects/car-monit-backend-jdk25 /mnt/d/work/IdeaProjects/car-monit-api-jdk17 /mnt/d/work/IdeaProjects/car-monit-api-jdk21 /mnt/d/work/IdeaProjects/car-monit-api-jdk25; do
  if [ -d "$d" ]; then
    printf '%s|%s|%s\n' "$d" "$(cd "$d" && git rev-parse --abbrev-ref HEAD 2>/dev/null)" "$(cd "$d" && git rev-parse --short HEAD 2>/dev/null)"
  fi
done
