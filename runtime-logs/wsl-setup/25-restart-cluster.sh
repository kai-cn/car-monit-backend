#!/usr/bin/env bash
set -u
LOG=/tmp/cluster-restart.log
echo "start $(date -Is)" > "$LOG"
/usr/local/bin/k3d cluster stop v3 >> "$LOG" 2>&1
sleep 5
/usr/local/bin/k3d cluster start v3 --wait --timeout 5m >> "$LOG" 2>&1
echo "START_RC=$?" >> "$LOG"
sleep 15
docker exec k3d-v3-server-0 kubectl get nodes >> "$LOG" 2>&1
echo "done $(date -Is)" >> "$LOG"
touch /tmp/cluster-restart.done
