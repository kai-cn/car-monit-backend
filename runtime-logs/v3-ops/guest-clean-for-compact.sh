#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Guest-side cleanup before VHDX compact. No volumes are deleted.
set -uo pipefail
echo "################ GUEST CLEAN $(date -Is) ################"
echo "==== docker system df BEFORE ===="
docker system df 2>&1
echo "==== images in use by containers ===="
docker ps -a --format '{{.Image}}' 2>/dev/null | sort -u
echo "==== explicitly retired application images ===="
# ci-v2 is the version currently referenced by the k3d deployments -> KEEP.
# car-monit-sys:local is the 152MB MySQL-free base -> KEEP.
# oracle_11g / mysql / opengauss / kafka / es / rancher / k3d -> KEEP (runtime or DB source).
RETIRED=(
  car-monit-api:ci-verify
  car-monit-backend:ci-verify
  car-monit-api:slim
  car-monit-backend:slim
  eclipse-temurin:17-jre
)
for img in "${RETIRED[@]}"; do
  if docker image inspect "$img" >/dev/null 2>&1; then
    echo "-- rmi $img"
    docker rmi "$img" 2>&1 | head -3 || echo "   (in use, left untouched)"
  else
    echo "-- absent $img"
  fi
done
echo "==== dangling prune ===="
docker image prune -f 2>&1 | tail -5
echo "==== builder cache prune ===="
docker builder prune -f 2>&1 | tail -5
echo "==== fstrim ===="
sudo fstrim -av 2>&1 | tail -10
echo "==== docker system df AFTER ===="
docker system df 2>&1
echo "==== remaining images ===="
docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' 2>&1
echo "################ END ################"
