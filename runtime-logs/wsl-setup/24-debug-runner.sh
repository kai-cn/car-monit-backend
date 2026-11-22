#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：24-debug-runner.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
systemctl stop actions-runner.service 2>/dev/null || true
pkill -9 -f '/opt/actions-runner/bin/Runner.Listener' 2>/dev/null || true
sleep 2
cd /opt/actions-runner
runuser -u dev -- timeout 20 ./run.sh > /tmp/runner-debug.log 2>&1
echo "RUN_RC=$?"
tail -20 /tmp/runner-debug.log
systemctl start actions-runner.service
