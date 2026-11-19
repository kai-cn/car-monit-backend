#!/usr/bin/env bash
set -u
LOG=/tmp/k3s-image.log
echo "start $(date -Is)" > "$LOG"
docker pull docker.1panel.live/rancher/k3s:v1.31.5-k3s1 >> "$LOG" 2>&1
echo "PULL_RC=$? $(date -Is)" >> "$LOG"
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' >> "$LOG" 2>&1
echo "done" >> "$LOG"
touch /tmp/k3s-image.done
