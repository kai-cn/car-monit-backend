#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "=== svc backend ==="
docker exec k3d-v3-server-0 kubectl get svc car-monit-backend -o wide 2>&1
echo "=== endpoints backend ==="
docker exec k3d-v3-server-0 kubectl get endpoints car-monit-backend 2>&1
echo "=== backend pod direct ==="
PODIP=$(docker exec k3d-v3-server-0 kubectl get pods -l app=car-monit-backend -o jsonpath='{.items[0].status.podIP}')
echo "pod ip=$PODIP"
docker exec k3d-v3-server-0 wget -qO- -T 6 http://$PODIP:9989/captchaImage 2>&1 | head -c 120
echo
echo "=== backend redis env ==="
docker exec k3d-v3-server-0 kubectl get deploy car-monit-backend -o yaml | grep -E 'SPRING_DATA_REDIS|CLUSTER' | head
echo "=== nodeport from WSL ==="
curl -s -m 6 -o /dev/null -w 'be30989=%{http_code}\n' http://172.18.0.5:30989/captchaImage
curl -s -m 6 -o /dev/null -w 'api30902=%{http_code}\n' http://172.18.0.5:30902/base/section/list
