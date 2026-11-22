# @description 历史脚本 sync-status-all.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage powershell -File sync-status-all.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Synchronize local and remote branches/worktrees; skips dirty user work.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Inventory Windows and WSL car-monit-* repositories: branch name and dirty-file count.

# Read-only diagnostic; safe to run before any sync or batch edit.

$ErrorActionPreference='Continue'

Write-Output '=== WINDOWS WORKTREES ==='

Get-ChildItem 'D:\work\IdeaProjects' -Directory | Where-Object { $_.Name -like 'car-monit-*' } | ForEach-Object {

  $p=$_.FullName

  if (Test-Path (Join-Path $p '.git')) {

    $b = & git -C $p rev-parse --abbrev-ref HEAD 2>$null

    $s = & git -C $p status --porcelain 2>$null

    $u = & git -C $p rev-parse '@{u}' 2>$null

    Write-Output ("{0,-42} branch={1,-34} dirty={2} upstream={3}" -f $_.Name,$b,@($s).Count,$u)

  }

}

Write-Output '=== WSL REPOS ==='

wsl.exe -d openEuler-24.03-LTS-SP4 -- bash -lc 'for d in /home/dev/IdeaProjects/car-monit-*; do [ -d "$d/.git" ] || continue; b=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null); s=$(git -C "$d" status --porcelain 2>/dev/null | wc -l); printf "%-42s branch=%-34s dirty=%s\n" "$(basename $d)" "$b" "$s"; done'

