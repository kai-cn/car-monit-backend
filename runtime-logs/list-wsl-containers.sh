#!/usr/bin/env bash
# @description 列出 WSL Docker 容器名称、状态和端口。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 07:38:02
# @usage bash runtime-logs/list-wsl-containers.sh
# @dependencies docker。
set -uo pipefail
docker ps -a --format '{{.Names}}|{{.Status}}|{{.Ports}}' | head -40
