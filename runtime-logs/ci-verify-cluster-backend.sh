#!/usr/bin/env bash

# @description 历史脚本 ci-verify-cluster-backend.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash ci-verify-cluster-backend.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 集群真实启动校验-backend：造镜像→k3d导入→set image→rollout→探活

set -euo pipefail

WORK=/tmp/ci-verify

IMG=car-monit-backend:ci-verify

cat > "$WORK/Dockerfile.backend" <<'EOF'

FROM eclipse-temurin:17-jre

RUN apt-get update && apt-get install -y --no-install-recommends fontconfig fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY car-monit-backend.jar /app/app.jar

ENTRYPOINT ["java","-jar","/app/app.jar"]

EOF

cd "$WORK"

echo "=== build ==="

docker build -f Dockerfile.backend -t "$IMG" . 2>&1 | tail -4

echo "=== k3d import ==="

k3d image import "$IMG" -c v3 2>&1 | tail -2

echo "=== set image + rollout ==="

docker exec k3d-v3-server-0 kubectl set image deployment/car-monit-backend backend="$IMG"

docker exec k3d-v3-server-0 kubectl rollout status deployment/car-monit-backend --timeout=300s

echo "=== health /captchaImage ==="

for i in $(seq 1 40); do

  code=$(curl -s -o /dev/null -w '%{http_code}' http://172.18.0.5:30989/captchaImage || true)

  if [ "$code" = "200" ]; then echo "CLUSTER_BACKEND_OK try=$i"; exit 0; fi

  sleep 3

done

echo "CLUSTER_BACKEND_FAIL"

docker exec k3d-v3-server-0 kubectl logs deployment/car-monit-backend --tail=40 || true

exit 1

