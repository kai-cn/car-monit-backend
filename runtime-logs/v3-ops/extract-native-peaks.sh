#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
for f in "$@"; do
  echo "=== $(basename "$f") ==="
  grep -oE '\([0-9]+\.[0-9]+s @ [0-9]+\.[0-9]+GB\)' "$f" | tail -3
  grep -m1 'Finished generating' "$f"
done
