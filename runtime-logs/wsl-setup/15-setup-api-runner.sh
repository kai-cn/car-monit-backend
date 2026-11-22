#!/usr/bin/env bash

# @description 历史脚本 15-setup-api-runner.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash 15-setup-api-runner.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# LEGACY-SCRIPT-ANNOTATION

# 文件：15-setup-api-runner.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

set -u

LOG=/tmp/api-runner.log

: "${RUNNER_TOK:?registration token missing}"

echo "start $(date -Is)" > "$LOG"

mkdir -p /opt/actions-runner-api

cp -a /opt/actions-runner/. /opt/actions-runner-api/

rm -f /opt/actions-runner-api/.runner /opt/actions-runner-api/.credentials \

      /opt/actions-runner-api/.credentials_rsaparams /opt/actions-runner-api/config.done \

      /opt/actions-runner-api/config.failed /opt/actions-runner-api/dl.done \

      /opt/actions-runner-api/dl.failed

rm -rf /opt/actions-runner-api/_work

chown -R dev:dev /opt/actions-runner-api

cd /opt/actions-runner-api || exit 1

runuser -u dev -- env RUNNER_TOK="$RUNNER_TOK" ./config.sh \

  --url https://github.com/kai-cn/car-monit-api \

  --token "$RUNNER_TOK" \

  --name wsl-k3s-api \

  --labels wsl-k3s-api \

  --unattended \

  --work _work \

  --replace > /tmp/api-runner-config.log 2>&1

echo "CONFIG_RC=$?" >> "$LOG"

cat > /etc/systemd/system/actions-runner-api.service <<'EOF'

[Unit]

Description=GitHub Actions Self-hosted Runner (car-monit-api / wsl-k3s-api)

After=network-online.target

Wants=network-online.target



[Service]

Type=simple

User=dev

Group=dev

WorkingDirectory=/opt/actions-runner-api

ExecStart=/opt/actions-runner-api/run.sh

Restart=always

RestartSec=15

KillMode=control-group

TimeoutStopSec=60



[Install]

WantedBy=multi-user.target

EOF

systemctl daemon-reload

systemctl enable --now actions-runner-api.service >> "$LOG" 2>&1

sleep 10

echo "SERVICE=$(systemctl is-active actions-runner-api.service)" >> "$LOG"

echo "done $(date -Is)" >> "$LOG"

touch /tmp/api-runner.done

