# @description 历史脚本 clean-local-package-worktrees.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage powershell -File clean-local-package-worktrees.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Purpose: remove only the temporary detached worktrees created for local packaging.

# Idea: read the generated manifest, map each worktree to its source repo, remove worktree records, then delete the temp root.

# Risk: scoped strictly to _local-package-<timestamp>; no source worktrees or user files are removed.

$ErrorActionPreference = 'Continue'

$root = Get-Content 'D:\work\runtime-logs\local-package-root.txt' -Raw -Encoding utf8

$root = $root.Trim()

$manifest = Get-Content 'D:\work\runtime-logs\local-package-manifest.tsv' -Encoding utf8

foreach ($line in $manifest) {

  if (-not $line) { continue }

  $parts = $line -split '\|'

  $wslPath = $parts[0]

  $app = $parts[1]

  $leaf = Split-Path $wslPath -Leaf

  $winPath = Join-Path $root $leaf

  $base = if ($app -eq 'backend') { 'D:\work\IdeaProjects\car-monit-backend-new' } else { 'D:\work\IdeaProjects\car-monit-api' }

  if (Test-Path $winPath) {

    & git -C $base worktree remove --force $winPath 2>&1 | Out-Null

    Write-Output "REMOVED $winPath"

  }

}

if (Test-Path $root) {

  Remove-Item -Recurse -Force $root -ErrorAction SilentlyContinue

  Write-Output "ROOT_REMOVED $root"

}

Get-PSDrive D | Select-Object Name,Used,Free

