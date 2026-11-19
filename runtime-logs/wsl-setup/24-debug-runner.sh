#!/usr/bin/env bash
systemctl stop actions-runner.service 2>/dev/null || true
pkill -9 -f '/opt/actions-runner/bin/Runner.Listener' 2>/dev/null || true
sleep 2
cd /opt/actions-runner
runuser -u dev -- timeout 20 ./run.sh > /tmp/runner-debug.log 2>&1
echo "RUN_RC=$?"
tail -20 /tmp/runner-debug.log
systemctl start actions-runner.service
