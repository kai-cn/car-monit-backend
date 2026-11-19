#!/usr/bin/env bash
set -u
LOG=/tmp/k3d-cluster.log
echo "start $(date -Is)" > "$LOG"
export PATH=/usr/local/bin:$PATH
k3d cluster create v3 \
  --servers 1 \
  --agents 2 \
  --image docker.1panel.live/rancher/k3s:v1.31.5-k3s1 \
  --wait --timeout 6m \
  --k3s-arg '--disable=traefik@server:0' \
  --k3s-arg '--disable=metrics-server@server:0' \
  --port '6443:6443@loadbalancer' >> "$LOG" 2>&1
echo "CREATE_RC=$?" >> "$LOG"
docker exec k3d-v3-server-0 kubectl get nodes -o wide >> "$LOG" 2>&1
echo "done $(date -Is)" >> "$LOG"
touch /tmp/k3d-cluster.done
