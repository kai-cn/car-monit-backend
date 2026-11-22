# @description 历史脚本 create-local-package-worktrees.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage powershell -File create-local-package-worktrees.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Purpose: create clean detached local worktrees for every Java branch to repackage.

# Idea: fetch current remote refs first, then add one detached worktree per branch with a safe directory name.

# Risk: creates new temporary worktrees under a timestamped directory; does not touch existing worktrees.

$ErrorActionPreference = 'Continue'

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

$root = "D:\work\IdeaProjects\_local-package-$stamp"

New-Item -ItemType Directory -Force -Path $root | Out-Null



$specs = @(

  @{ repo='D:\work\IdeaProjects\car-monit-backend-new'; app='backend'; branch='master'; jdk='8' },

  @{ repo='D:\work\IdeaProjects\car-monit-backend-new'; app='backend'; branch='car-monit-backend-java-V3'; jdk='8' },

  @{ repo='D:\work\IdeaProjects\car-monit-backend-new'; app='backend'; branch='feat/backend-full-parity'; jdk='8' },

  @{ repo='D:\work\IdeaProjects\car-monit-backend-new'; app='backend'; branch='car-monit-backend-jdk17'; jdk='17' },

  @{ repo='D:\work\IdeaProjects\car-monit-backend-new'; app='backend'; branch='car-monit-backend-jdk21'; jdk='21' },

  @{ repo='D:\work\IdeaProjects\car-monit-backend-new'; app='backend'; branch='car-monit-backend-jdk25'; jdk='25' },

  @{ repo='D:\work\IdeaProjects\car-monit-backend-new'; app='backend'; branch='feature-dbupgrade'; jdk='25' },

  @{ repo='D:\work\IdeaProjects\car-monit-api'; app='api'; branch='master'; jdk='8' },

  @{ repo='D:\work\IdeaProjects\car-monit-api'; app='api'; branch='car-monit-api-java-V3'; jdk='8' },

  @{ repo='D:\work\IdeaProjects\car-monit-api'; app='api'; branch='car-monit-api-java-fix'; jdk='8' },

  @{ repo='D:\work\IdeaProjects\car-monit-api'; app='api'; branch='feature/springboot3-jdk17'; jdk='17' },

  @{ repo='D:\work\IdeaProjects\car-monit-api'; app='api'; branch='feature/springboot3'; jdk='21' },

  @{ repo='D:\work\IdeaProjects\car-monit-api'; app='api'; branch='car-monit-api-jdk17'; jdk='17' },

  @{ repo='D:\work\IdeaProjects\car-monit-api'; app='api'; branch='car-monit-api-jdk21'; jdk='21' },

  @{ repo='D:\work\IdeaProjects\car-monit-api'; app='api'; branch='car-monit-api-jdk25'; jdk='25' },

  @{ repo='D:\work\IdeaProjects\car-monit-api'; app='api'; branch='feature-dbupgrade'; jdk='25' }

)



foreach ($repo in @('D:\work\IdeaProjects\car-monit-backend-new','D:\work\IdeaProjects\car-monit-api')) {

  & git -C $repo fetch origin 2>&1 | Out-Null

}



$lines = @()

foreach ($s in $specs) {

  $safe = ($s.app + '__' + $s.branch) -replace '[^A-Za-z0-9._-]', '_'

  $path = Join-Path $root $safe

  $wslPath = '/mnt/d/work/IdeaProjects/' + (Split-Path $root -Leaf) + '/' + $safe

  & git -C $s.repo worktree add --detach $path "refs/remotes/origin/$($s.branch)" 2>&1 | Out-Null

  $sha = & git -C $path rev-parse --short HEAD

  $module = if ($s.app -eq 'backend') { 'ruoyi-admin' } else { 'pro-business-api' }

  $lines += "$wslPath|$($s.app)|$($s.jdk)|$($s.branch)|$module|$sha"

  Write-Output "ADDED $($s.app) $($s.branch) $sha"

}

$manifest = 'D:\work\runtime-logs\local-package-manifest.tsv'

$lines | Set-Content -Path $manifest -Encoding utf8

[System.IO.File]::WriteAllText('D:\work\runtime-logs\local-package-root.txt', $root)

Write-Output "MANIFEST $manifest"

