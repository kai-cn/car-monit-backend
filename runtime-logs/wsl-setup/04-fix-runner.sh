#!/usr/bin/env bash
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
