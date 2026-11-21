# LEGACY-SCRIPT-ANNOTATION
# 文件：car-monit-backend-jdk17_b5.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set -euo pipefail
if ! docker info >/dev/null 2>&1; then
  echo ">> docker daemon down, attempting to start it"
  sudo -n systemctl start docker 2>/dev/null || true
  for i in $(seq 1 12); do
    docker info >/dev/null 2>&1 && break
    sleep 5
  done
fi
docker info >/dev/null 2>&1 || {
  echo "::error::docker daemon unavailable on the self-hosted runner"
  exit 1
}
RUNNING="$(docker ps --format '{{.Names}}' 2>/dev/null || true)"
PRESENT="$(docker ps -a --format '{{.Names}}' 2>/dev/null || true)"
for c in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do
  if grep -Fxq -- "${c}" <<< "${RUNNING}"; then
    echo "${c}: already running"
  elif grep -Fxq -- "${c}" <<< "${PRESENT}"; then
    echo "${c}: starting"
    docker start "${c}" || true
  else
    echo "::warning::${c}: container not found (cluster may need recreation)"
  fi
done
for i in $(seq 1 24); do
  if docker exec k3d-v3-server-0 kubectl get nodes >/dev/null 2>&1; then
    echo "k3d cluster API ready"
    exit 0
  fi
  sleep 5
done
echo "::error::k3d cluster API did not become ready within 120s"
exit 1


