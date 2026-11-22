#!/usr/bin/env bash

# @description 历史脚本 ci-verify-cluster-both.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash ci-verify-cluster-both.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 集群真实部署校验（backend + api）：基于 :slim 基座换 jar → k3d 导入 → set image → rollout → 动态IP探活

set -euo pipefail

WORK=/tmp/ci-verify

cd "$WORK"

cat > Dockerfile.backend <<'EOF'

FROM car-monit-backend:slim

COPY car-monit-backend.jar /app/app.jar

EOF

cat > Dockerfile.api <<'EOF'

FROM car-monit-api:slim

COPY car-monit-api.jar /app/app.jar

EOF

TAG=ci-v2

echo "=== build（基于 slim 换 jar）==="

docker build -f Dockerfile.backend -t car-monit-backend:$TAG . 2>&1 | tail -2

docker build -f Dockerfile.api -t car-monit-api:$TAG . 2>&1 | tail -2

echo "=== import ==="

k3d image import car-monit-backend:$TAG car-monit-api:$TAG -c v3 2>&1 | tail -1

echo "=== backend set image + rollout ==="

docker exec k3d-v3-server-0 kubectl set image deployment/car-monit-backend backend=car-monit-backend:$TAG

docker exec k3d-v3-server-0 kubectl rollout status deployment/car-monit-backend --timeout=360s

echo "=== api set image + rollout ==="

docker exec k3d-v3-server-0 kubectl set image deployment/car-monit-api api=car-monit-api:$TAG

docker exec k3d-v3-server-0 kubectl rollout status deployment/car-monit-api --timeout=360s

echo "=== health（动态 server IP）==="

NODE_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' k3d-v3-server-0)

echo "server=${NODE_IP}"

bo=1; ao=1

for i in $(seq 1 40); do c=$(curl -s -o /dev/null -w '%{http_code}' "http://${NODE_IP}:30989/captchaImage" || true); [ "$c" = "200" ] && { echo "backend=200 try=$i"; bo=0; break; }; sleep 3; done

[ "$bo" = 1 ] && echo "backend=FAIL"

for i in $(seq 1 40); do c=$(curl -s -o /dev/null -w '%{http_code}' "http://${NODE_IP}:30902/base/section/list" || true); [ "$c" = "200" ] && { echo "api=200 try=$i"; ao=0; break; }; sleep 3; done

[ "$ao" = 1 ] && echo "api=FAIL"

if [ "$bo" = 0 ] && [ "$ao" = 0 ]; then echo "CLUSTER_BOTH_OK"; exit 0; fi

docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide || true

exit 1

