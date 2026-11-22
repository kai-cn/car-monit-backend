#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Synchronize local and remote branches/worktrees; skips dirty user work.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 将参数化模板同步到各 JDK 分支的 .github/workflows/self-hosted-ci.yml
set -euo pipefail
TPL_B=/mnt/d/work/runtime-logs/tpl-backend-selfhosted-ci.yml
TPL_A=/mnt/d/work/runtime-logs/tpl-api-selfhosted-ci.yml
ROOT=/mnt/d/work/IdeaProjects

gen() { # tpl dir java branches
  local tpl="$1" dir="$2" java="$3" branches="$4"
  local out="$dir/.github/workflows/self-hosted-ci.yml"
  [ -d "$dir" ] || { echo "SKIP(no dir) $dir"; return 0; }
  mkdir -p "$dir/.github/workflows"
  sed -e "s|__JAVA_MAJOR__|$java|g" -e "s|__BRANCHES__|$branches|g" "$tpl" > "$out"
  echo "OK  java=$java  $out"
}

# ---- backend (ruoyi-admin, 9989, wsl-k3s) ----
gen "$TPL_B" "$ROOT/car-monit-backend-jdk17"   17 "[car-monit-backend-java-V3, car-monit-backend-jdk17]"
gen "$TPL_B" "$ROOT/car-monit-backend-jdk21"   21 "[car-monit-backend-java-V3, car-monit-backend-jdk21]"
gen "$TPL_B" "$ROOT/car-monit-backend-jdk25"   25 "[car-monit-backend-java-V3, car-monit-backend-jdk25]"
gen "$TPL_B" "$ROOT/car-monit-backend-java-V3"  8 "[car-monit-backend-java-V3]"

# ---- api (pro-business-api, 9902, wsl-k3s-api) ----
gen "$TPL_A" "$ROOT/car-monit-api-java-V3" 8 "[car-monit-api-java-V3, car-monit-api-jdk17, car-monit-api-jdk21, car-monit-api-jdk25]"
gen "$TPL_A" "$ROOT/car-monit-api-jdk17"  17 "[car-monit-api-java-V3, car-monit-api-jdk17]"
gen "$TPL_A" "$ROOT/car-monit-api-jdk21"  21 "[car-monit-api-java-V3, car-monit-api-jdk21]"
gen "$TPL_A" "$ROOT/car-monit-api-jdk25"  25 "[car-monit-api-java-V3, car-monit-api-jdk25]"

echo "---- done ----"
