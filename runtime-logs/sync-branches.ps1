# @description 历史脚本 sync-branches.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage powershell -File sync-branches.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Synchronize local and remote branches/worktrees; skips dirty user work.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Synchronize every Windows car-monit-* worktree with its fetched remote tracking branch.

# Fast-forwards when possible; merges with -X theirs when local and remote diverged.

# Dirty worktrees (tracked user changes) are skipped and never overwritten.

$ErrorActionPreference='Continue'

Get-ChildItem 'D:\work\IdeaProjects' -Directory | Where-Object { $_.Name -like 'car-monit-*' } | ForEach-Object {

  $p=$_.FullName

  if (-not (Test-Path (Join-Path $p '.git'))) { return }

  $br = & git -C $p rev-parse --abbrev-ref HEAD 2>$null

  if (-not $br -or $br -eq 'HEAD') { Write-Output "SKIP detached $($_.Name)"; return }

  $dirty = @(& git -C $p status --porcelain 2>$null | Where-Object { $_ -notmatch '^\?\?' })

  if ($dirty.Count -gt 0) { Write-Output "SKIP dirty $($_.Name) ($($dirty.Count) tracked changes)"; return }

  & git -C $p fetch origin --prune 2>$null | Out-Null

  $ref = "origin/$br"

  $ok = & git -C $p rev-parse --verify --quiet $ref 2>$null

  if (-not $ok) { Write-Output "SKIP no-upstream $($_.Name) $br"; return }

  $counts = (& git -C $p rev-list --left-right --count "$ref...HEAD" 2>$null).Trim().Split()

  $behind=[int]$counts[0]; $ahead=[int]$counts[1]

  if ($behind -eq 0) { Write-Output "OK $($_.Name) $br ahead=$ahead"; return }

  if ($ahead -eq 0) {

    & git -C $p merge --ff-only $ref 2>&1 | Out-Null

    Write-Output "FF $($_.Name) $br behind=$behind"

  } else {

    & git -C $p merge -X theirs $ref -m 'merge remote workflow optimization' 2>&1 | Out-Null

    $rc=$LASTEXITCODE

    Write-Output "MERGE $($_.Name) $br behind=$behind ahead=$ahead rc=$rc"

  }

}

