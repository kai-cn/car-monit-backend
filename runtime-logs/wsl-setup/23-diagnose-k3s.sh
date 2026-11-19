#!/usr/bin/env bash
for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1 k3d-v3-serverlb; do
  echo "==== $n ===="
  docker inspect "$n" | jq '.[0] | {RestartCount, Status: .State.Status, ExitCode: .State.ExitCode, OOM: .State.OOMKilled, Error: .State.Error, RestartPolicy: .HostConfig.RestartPolicy.Name}'
  docker logs "$n" --tail 5 2>&1 | tail -5
done
echo "==== MEM ===="
free -m | head -3
echo "==== OOM in dmesg ===="
dmesg 2>/dev/null | grep -i -E 'oom|killed process' | tail -8
