#!/usr/bin/env bash
set -u
LOG=/tmp/k3d-install.log
VER=v5.9.0
echo "start $(date -Is)" > "$LOG"
curl -fsSL --retry 3 --max-time 300 -o /usr/local/bin/k3d \
  "https://github.com/k3d-io/k3d/releases/download/$VER/k3d-linux-amd64" >> "$LOG" 2>&1
echo "CURL_RC=$?" >> "$LOG"
chmod +x /usr/local/bin/k3d
/usr/local/bin/k3d version >> "$LOG" 2>&1
echo "done $(date -Is)" >> "$LOG"
touch /tmp/k3d-install.done
