#!/usr/bin/env bash
# @description 定位 WSL backend master 的 GenController column 方法签名并查看当前差异统计。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 01:00:50
# @usage bash runtime-logs/wsl-gen-controller-check.sh
# @dependencies WSL backend master clone。
set -uo pipefail
grep -n 'column' /home/dev/IdeaProjects/car-monit-backend/ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java | head -10
echo STATUS
git -C /home/dev/IdeaProjects/car-monit-backend diff --stat
git -C /home/dev/IdeaProjects/car-monit-api diff --stat
