#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== WSL docker container memory limits ==="
for c in mysql_wsl opengauss k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do
  docker inspect --format '{{.Name}} mem={{.HostConfig.Memory}} status={{.State.Status}}' "$c" 2>/dev/null || true
done
echo "=== WSL init / systemd ==="
ps -p 1 -o comm= 2>/dev/null || true
systemctl is-system-running 2>&1 | head -2
echo "=== package availability (no install) ==="
rpm -q fontconfig dejavu-sans-fonts tcl jemalloc-devel 2>/dev/null | head -8
echo "=== WSL disk ==="
df -h / /srv 2>/dev/null | head -4
echo "=== local redis tarballs / sources ==="
find /home/dev /srv /tmp -maxdepth 3 -iname 'redis-*.tar.gz' 2>/dev/null | head -5
echo "=== dnf repo reachable? (metadata only) ==="
timeout 15 dnf -q list --available fontconfig 2>&1 | head -4
