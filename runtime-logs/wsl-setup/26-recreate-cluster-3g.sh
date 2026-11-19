#!/usr/bin/env bash
set -u
LOG=/tmp/k3d-recreate.log
REG=/mnt/d/work/runtime-logs/wsl-setup/k3d-registries.yaml
echo "start $(date -Is)" > "$LOG"
sed -i 's/\r$//' "$REG"
/usr/local/bin/k3d cluster delete v3 >> "$LOG" 2>&1
sleep 3
/usr/local/bin/k3d cluster create v3 \
  --servers 1 \
  --agents 2 \
  --image rancher/k3s:v1.35.5-k3s1 \
  --registry-config "$REG" \
  --k3s-arg '--disable=traefik@server:0' \
  --k3s-arg '--disable=metrics-server@server:0' \
  --port '6443:6443@loadbalancer' \
  --wait --timeout 6m >> "$LOG" 2>&1
echo "CREATE_RC=$? $(date -Is)" >> "$LOG"
docker exec k3d-v3-server-0 kubectl get nodes >> "$LOG" 2>&1
docker exec k3d-v3-server-0 kubectl get pods -A >> "$LOG" 2>&1
echo "done" >> "$LOG"
touch /tmp/k3d-recreate.done
