#!/usr/bin/env bash
set -u
LOG=/tmp/k3d-registries.log
echo "start $(date -Is)" > "$LOG"
cp /mnt/d/work/runtime-logs/wsl-setup/k3d-registries.yaml /tmp/registries.yaml
sed -i 's/\r$//' /tmp/registries.yaml
for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do
  docker exec "$n" mkdir -p /etc/rancher/k3s
  docker cp /tmp/registries.yaml "$n":/etc/rancher/k3s/registries.yaml
  echo "copied to $n" >> "$LOG"
done
for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do
  docker restart "$n" >> "$LOG" 2>&1
  echo "restarted $n" >> "$LOG"
done
echo "restart done $(date -Is)" >> "$LOG"
sleep 75
docker exec k3d-v3-server-0 kubectl get nodes >> "$LOG" 2>&1
docker exec k3d-v3-server-0 kubectl get pods -A >> "$LOG" 2>&1
echo "done $(date -Is)" >> "$LOG"
touch /tmp/k3d-registries.done
