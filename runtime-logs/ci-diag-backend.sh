#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== pods ==="
docker exec k3d-v3-server-0 kubectl get pods -l app=car-monit-backend -o wide
PODIP=$(docker exec k3d-v3-server-0 kubectl get pods -l app=car-monit-backend -o jsonpath='{.items[0].status.podIP}')
echo "podip=$PODIP"
echo "=== pod 直连 9989 ==="
docker exec k3d-v3-server-0 wget -qO- -T 6 "http://${PODIP}:9989/captchaImage" 2>&1 | head -c 160
echo
echo "=== 容器实际命令(ENTRYPOINT+args 叠加检查) ==="
docker exec k3d-v3-server-0 kubectl get deployment car-monit-backend -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}' 2>/dev/null || true
echo "=== logs tail ==="
docker exec k3d-v3-server-0 kubectl logs deployment/car-monit-backend --tail=20 2>&1
