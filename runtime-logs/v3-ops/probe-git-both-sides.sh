#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only diagnostic: inspect state, logs, or environment without modifying the target.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
echo "========== WSL IdeaProjects git 状态 =========="
for d in /home/dev/IdeaProjects/car-monit-*; do
  [[ -d "$d" ]] || continue
  name=$(basename "$d")
  printf '%-42s ' "$name"
  if [[ -f "$d/.git" ]]; then
    printf 'gitfile->%s' "$(sed -n 's/^gitdir: //p' "$d/.git")"
  elif [[ -d "$d/.git" ]]; then
    br=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null || echo GIT_ERROR)
    printf 'DIR branch=%s' "$br"
  else
    printf 'NO_GIT'
  fi
  echo
done
echo "========== Windows 侧 git 状态 =========="
for d in /mnt/d/work/IdeaProjects/car-monit-*; do
  [[ -d "$d/.git" || -f "$d/.git" ]] || continue
  br=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null || echo GIT_ERROR)
  printf '%-52s %s\n' "$(basename "$d")" "$br"
done
