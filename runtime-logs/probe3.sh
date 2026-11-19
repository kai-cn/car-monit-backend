#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
echo "=== tools in k3d node ==="
for c in bash sh wget curl nc timeout python3 tar; do printf "%s: " "$c"; docker exec k3d-v3-server-0 sh -c "command -v $c || echo missing"; done
echo "=== raw /dev/tcp gateway test ==="
docker exec k3d-v3-server-0 bash -c 'echo > /dev/tcp/172.18.0.1/3307' 2>&1 | head -3
echo "rc=$?"
echo "=== all docker images ==="
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' 2>/dev/null | head -30
echo "=== linux JDK tarballs / extracted dirs in WSL ==="
find /opt /srv /root /home /tmp -maxdepth 4 \( -iname 'OpenJDK*linux*.tar.gz' -o -iname 'jdk-17*' -o -iname 'jdk-21*' -o -iname 'jdk-25*' -o -iname 'bin/java' \) 2>/dev/null | head -30
echo "=== WSL java ==="
java -version 2>&1 | head -3 || true
command -v java || true
echo "=== containerd images in k3d node ==="
docker exec k3d-v3-server-0 ctr images ls 2>/dev/null | head -15
