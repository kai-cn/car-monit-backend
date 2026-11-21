#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：05-clean-runner.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set -u
systemctl stop actions-runner.service || true
pkill -9 -f '/opt/actions-runner/bin/Runner.Listener' || true
pkill -9 -f '/opt/actions-runner/run-helper.sh' || true
sleep 2
cp /mnt/d/work/runtime-logs/wsl-setup/actions-runner.service /etc/systemd/system/actions-runner.service
sed -i 's/\r$//' /etc/systemd/system/actions-runner.service
systemctl daemon-reload
systemctl start actions-runner.service
sleep 12
echo "=== service ==="
systemctl is-active actions-runner.service
echo "=== listener processes ==="
pgrep -af '/opt/actions-runner/bin/Runner.Listener' || true
echo "=== recent log ==="
journalctl -u actions-runner.service --no-pager -n 12 | tail -12
