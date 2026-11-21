#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Read-only environment probe for the native-image / CI work.
set -uo pipefail
EP=unix:///run/k3s/containerd/containerd.sock
NODES=(k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1)

echo "==== TS ===="; date -Is
echo "==== OS / CPU / MEM ===="; uname -a; head -4 /etc/os-release; echo "nproc=$(nproc)"; free -m
echo "==== DF ===="; df -h / /mnt/d 2>/dev/null
echo "==== DOCKER ===="
docker version --format 'client={{.Client.Version}} server={{.Server.Version}}' 2>&1
docker info --format 'driver={{.Driver}} root={{.DockerRootDir}}' 2>&1
docker system df 2>&1
echo "-- images --"; docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}' 2>&1
echo "-- dangling --"; docker images -f dangling=true --format '{{.ID}} {{.Size}}' 2>&1
echo "-- containers --"; docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' 2>&1

echo "==== K3D ===="
k3d cluster list 2>&1
docker exec k3d-v3-server-0 kubectl get nodes -o wide 2>&1
echo "-- deploy --"; docker exec k3d-v3-server-0 kubectl get deploy -o wide 2>&1 | head -20
echo "-- pods --"; docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide 2>&1 | head -20
echo "-- in-use imageID --"; docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .status.containerStatuses[*]}{.image}{"\t"}{.imageID}{"\n"}{end}{end}' 2>&1
for n in "${NODES[@]}"; do
  echo "-- crictl images $n --"
  docker exec "$n" crictl --runtime-endpoint "$EP" images 2>&1 | grep -E 'IMAGE|car-monit' || echo "(none / crictl failed)"
done

echo "==== JAVA / MAVEN / NATIVE TOOLCHAIN (WSL) ===="
echo "JAVA_HOME=${JAVA_HOME:-<unset>}"
for c in java javac mvn native-image gu jlink jdeps; do printf '%-12s %s\n' "$c" "$(command -v "$c" 2>/dev/null || echo MISSING)"; done
java -version 2>&1 | head -3
mvn -v 2>&1 | head -4
echo "-- ci-toolchain cache --"; ls -la /home/dev/.cache/ci-toolchain/ 2>/dev/null | head -30
echo "-- native-image binaries (limited depth) --"
find /home /opt /usr/lib/jvm -maxdepth 5 -name 'native-image' -type f 2>/dev/null | head -20
echo "-- GraalVM/Mandrel dirs in WSL --"
find /home /opt -maxdepth 4 -type d \( -iname '*mandrel*' -o -iname '*graalvm*' \) 2>/dev/null | head -20

echo "==== D:\jdk MANDREL (mounted from Windows) ===="
ls -d /mnt/d/jdk/mandrel* 2>/dev/null
for d in /mnt/d/jdk/mandrel*; do
  [ -d "$d" ] || continue
  echo "-- $d --"
  ls -la "$d" 2>/dev/null | head -14
  ls "$d/bin" 2>/dev/null | head -25
  echo "   release:"; head -6 "$d/release" 2>/dev/null
done
echo "-- native-image.* files under /mnt/d/jdk --"
find /mnt/d/jdk -maxdepth 4 \( -name 'native-image' -o -name 'native-image.cmd' -o -name 'native-image.exe' \) 2>/dev/null | head -20

echo "==== CI RUNNER ===="
systemctl is-active actions-runner.service actions-runner-api.service docker 2>&1
ls -la /home/dev/actions-runner* 2>/dev/null | head -10

echo "==== DISK HOTSPOTS ===="
du -sh /var/lib/docker /var/lib/docker/overlay2 /home/dev /var/lib/rancher 2>/dev/null
echo "-- largest dirs under /var/lib/docker --"
du -sh /var/lib/docker/* 2>/dev/null | sort -rh | head -12
echo "==== END ===="
