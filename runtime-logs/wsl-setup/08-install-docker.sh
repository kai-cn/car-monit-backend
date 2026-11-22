#!/usr/bin/env bash

# @description 历史脚本 08-install-docker.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash 08-install-docker.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION

# 文件：08-install-docker.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

set -u

LOG=/tmp/k3s-docker-install.log

echo "start $(date -Is)" > "$LOG"

dnf install -y moby moby-client iptables >> "$LOG" 2>&1

echo "DNF_RC=$? $(date -Is)" >> "$LOG"

mkdir -p /etc/docker

cat > /etc/docker/daemon.json <<'EOF'

{

  "registry-mirrors": ["https://docker.m.daocloud.io", "https://docker.1panel.live"]

}

EOF

systemctl enable --now docker >> "$LOG" 2>&1

sleep 6

echo "DOCKER_ACTIVE=$(systemctl is-active docker)" >> "$LOG"

docker version --format '{{.Server.Version}}' >> "$LOG" 2>&1

docker info --format 'CgroupDriver={{.CgroupDriver}} Storage={{.Driver}}' >> "$LOG" 2>&1

echo "done $(date -Is)" >> "$LOG"

touch /tmp/k3s-docker-install.done

