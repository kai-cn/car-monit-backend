#!/usr/bin/env bash
set -u
LOG=/tmp/k3s-docker-install.log
echo "start $(date -Is)" > "$LOG"
dnf install -y moby moby-client iptables >> "$LOG" 2>&1
echo "DNF_RC=$? $(date -Is)" >> "$LOG"
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": ["https://docker.m.daocloud.io", "https://docker.1panel.live"]
}
EOF
systemctl enable --now docker >> "$LOG" 2>&1
sleep 6
echo "DOCKER_ACTIVE=$(systemctl is-active docker)" >> "$LOG"
docker version --format '{{.Server.Version}}' >> "$LOG" 2>&1
docker info --format 'CgroupDriver={{.CgroupDriver}} Storage={{.Driver}}' >> "$LOG" 2>&1
echo "done $(date -Is)" >> "$LOG"
touch /tmp/k3s-docker-install.done
