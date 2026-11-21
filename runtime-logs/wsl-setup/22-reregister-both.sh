#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：22-reregister-both.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set -u
: "${TOK_BE:?backend token missing}"
: "${TOK_API:?api token missing}"
pkill -9 -f '/opt/actions-runner/bin/Runner.Listener' 2>/dev/null || true
pkill -9 -f '/opt/actions-runner-api/bin/Runner.Listener' 2>/dev/null || true
systemctl stop actions-runner.service actions-runner-api.service 2>/dev/null || true
sleep 2

rereg() {
  dir=$1; repo=$2; name=$3; svc=$4; tok=$5
  cd "$dir" || return 1
  rm -f .runner .credentials .credentials_rsaparams config.done config.failed
  chown -R dev:dev "$dir"
  runuser -u dev -- env RUNNER_TOK="$tok" ./config.sh \
    --url "https://github.com/$repo" \
    --token "$tok" \
    --name "$name" \
    --labels "$name" \
    --unattended \
    --work _work \
    --replace > "/tmp/rereg-$name.log" 2>&1
  echo "$name CONFIG_RC=$?"
  systemctl start "$svc"
}

rereg /opt/actions-runner kai-cn/car-monit-backend wsl-k3s actions-runner.service "$TOK_BE"
rereg /opt/actions-runner-api kai-cn/car-monit-api wsl-k3s-api actions-runner-api.service "$TOK_API"
sleep 10
echo "=== services ==="
systemctl is-active actions-runner.service actions-runner-api.service
echo "=== logs ==="
tail -3 /tmp/rereg-wsl-k3s.log
tail -3 /tmp/rereg-wsl-k3s-api.log
