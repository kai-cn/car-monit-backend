#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：04-fix-runner.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set -u
echo "=== listeners before ==="
pgrep -af 'Runner.Listener' || true
echo "=== restart service ==="
systemctl restart actions-runner.service
sleep 10
echo "=== service ==="
systemctl is-active actions-runner.service
systemctl show actions-runner.service -p MainPID -p NRestarts
echo "=== listeners after ==="
pgrep -af 'Runner.Listener' || true
echo "=== recent log ==="
journalctl -u actions-runner.service --no-pager -n 18 | tail -18
