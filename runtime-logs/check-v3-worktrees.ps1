# LEGACY-SCRIPT-ANNOTATION
# 文件：check-v3-worktrees.ps1
# 用途：只读检查/诊断。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：通常只读；若脚本内有明确写操作以其自身说明为准。
# 只读检查所有 V3 相关工作树的分支、ahead/behind 与脏文件数。
$roots = Get-ChildItem 'D:\work\IdeaProjects' -Directory | Where-Object { Test-Path (Join-Path $_.FullName '.git') }
foreach ($r in $roots) {
  $wt = & git -C $r.FullName worktree list --porcelain 2>$null
  if (-not $wt) { continue }
  $paths = @()
  foreach ($line in $wt) { if ($line -like 'worktree *') { $paths += $line.Substring(9) } }
  foreach ($p in $paths) {
    $b = & git -C $p rev-parse --abbrev-ref HEAD 2>$null
    if ($b -notlike '*V3*') { continue }
    $ab = & git -C $p rev-list --left-right --count '@{u}...HEAD' 2>$null
    $dirty = (& git -C $p status --porcelain 2>$null | Measure-Object).Count
    Write-Output "$p | branch=$b | ahead_behind=$ab | dirty=$dirty"
  }
}
