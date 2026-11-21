#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：23-diagnose-k3s.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1 k3d-v3-serverlb; do
  echo "==== $n ===="
  docker inspect "$n" | jq '.[0] | {RestartCount, Status: .State.Status, ExitCode: .State.ExitCode, OOM: .State.OOMKilled, Error: .State.Error, RestartPolicy: .HostConfig.RestartPolicy.Name}'
  docker logs "$n" --tail 5 2>&1 | tail -5
done
echo "==== MEM ===="
free -m | head -3
echo "==== OOM in dmesg ===="
dmesg 2>/dev/null | grep -i -E 'oom|killed process' | tail -8
