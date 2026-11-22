#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -u
for n in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do
  echo "--- $n ---"
  docker exec "$n" crictl stats -o json 2>/dev/null | jq -r '.stats[]? | select(.attributes.metadata.name | test("backend|api")) | [.attributes.metadata.name, (.memory.workingSetBytes.value // "null" | tostring), (.memory.usageBytes.value // "null" | tostring)] | @tsv' 2>/dev/null | head -6
done
