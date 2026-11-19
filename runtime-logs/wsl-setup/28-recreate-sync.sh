#!/usr/bin/env bash
set -u
REG=/mnt/d/work/runtime-logs/wsl-setup/k3d-registries.yaml
sed -i 's/\r$//' "$REG"
echo "=== deleting old cluster ==="
/usr/local/bin/k3d cluster delete v3
echo "=== creating cluster ==="
/usr/local/bin/k3d cluster create v3 \
  --servers 1 \
  --agents 2 \
  --image rancher/k3s:v1.35.5-k3s1 \
  --registry-config "$REG" \
  --k3s-arg '--disable=traefik@server:0' \
  --k3s-arg '--disable=metrics-server@server:0' \
  --port '6443:6443@loadbalancer' \
  --wait --timeout 6m
echo "CREATE_RC=$?"
echo "=== nodes ==="
docker exec k3d-v3-server-0 kubectl get nodes
echo "=== system pods ==="
docker exec k3d-v3-server-0 kubectl get pods -A
