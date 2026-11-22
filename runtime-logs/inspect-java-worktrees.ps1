# @description 历史脚本 inspect-java-worktrees.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage powershell -File inspect-java-worktrees.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Purpose: inspect local Java worktrees before local repackaging.

# Idea: report branch, dirty state, and upstream delta so builds do not silently use stale code.

# Risk: read-only; no fetch, checkout, reset, or file modification.

$paths = @(

  'D:\work\IdeaProjects\car-monit-backend-new',

  'D:\work\IdeaProjects\car-monit-backend-java-V3',

  'D:\work\IdeaProjects\car-monit-backend-jdk17',

  'D:\work\IdeaProjects\car-monit-backend-jdk21',

  'D:\work\IdeaProjects\car-monit-backend-jdk25',

  'D:\work\IdeaProjects\car-monit-api',

  'D:\work\IdeaProjects\car-monit-api-java-V3',

  'D:\work\IdeaProjects\car-monit-api-java-fix',

  'D:\work\IdeaProjects\car-monit-api-jdk17',

  'D:\work\IdeaProjects\car-monit-api-jdk21',

  'D:\work\IdeaProjects\car-monit-api-jdk25'

)

foreach ($p in $paths) {

  if (-not (Test-Path $p)) { Write-Output "$p|MISSING"; continue }

  $b = & git -C $p rev-parse --abbrev-ref HEAD 2>$null

  $h = & git -C $p rev-parse --short HEAD 2>$null

  $d = (& git -C $p status --porcelain 2>$null | Measure-Object).Count

  $ab = & git -C $p rev-list --left-right --count '@{u}...HEAD' 2>$null

  Write-Output "$p|branch=$b|head=$h|dirty=$d|aheadbehind=$ab"

}

