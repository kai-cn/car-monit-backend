# @description 历史脚本 optimize-workflows-cloud.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage powershell -File optimize-workflows-cloud.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Maven 与对应 JDK
# LEGACY-SCRIPT-ANNOTATION

# 文件：optimize-workflows-cloud.ps1

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

# Performance pass over every workflow on every branch of one repository.

# Usage: optimize-workflows-cloud.ps1 -RepoFull <owner/repo>

# Changes: cancel superseded runs, run parity matrix in parallel, fastest artifact compression,

# and cache: maven for setup-java jobs. Security invariants are checked separately by

# verify_remote_hardening.py after this script runs.

param(

  [Parameter(Mandatory=$true)][string]$RepoFull  # kai-cn/car-monit-api | kai-cn/car-monit-backend

)

$ErrorActionPreference='Continue'

$repoShort = $RepoFull.Split('/')[-1]

$tmp = Join-Path $env:TEMP "wfopt_$repoShort"

New-Item -ItemType Directory -Force -Path $tmp | Out-Null



function Api([string]$method,[string]$uri,[string]$bodyFile=$null) {

  if ($bodyFile) { return (& 'D:\work\runtime-logs\gh_api.ps1' -Method $method -Uri $uri -BodyFile $bodyFile | Out-String) }

  return (& 'D:\work\runtime-logs\gh_api.ps1' -Method $method -Uri $uri | Out-String)

}



$branchesRaw = Api GET "https://api.github.com/repos/$RepoFull/branches?per_page=100"

$branches = @()

foreach ($m in [regex]::Matches($branchesRaw, '"name":\s+"([^"]+)"')) { $branches += $m.Groups[1].Value }

Write-Output "REPO=$RepoFull branches=$($branches.Count)"



$changedCount = 0

foreach ($br in $branches) {

  $encBr = [uri]::EscapeDataString($br)

  $wfRaw = Api GET "https://api.github.com/repos/$RepoFull/contents/.github/workflows?ref=$encBr"

  $paths = @()

  foreach ($m in [regex]::Matches($wfRaw, '"path":\s+"([^"]+\.ya?ml)"')) {

    $paths += $m.Groups[1].Value

  }

  if ($br -eq 'master') { Write-Output "DEBUG master paths=$($paths.Count) wfLen=$($wfRaw.Length)" }

  foreach ($p in $paths) {

    $local = Join-Path $tmp ("f_" + [guid]::NewGuid().ToString('N') + ".yml")

    & 'D:\work\runtime-logs\fetch-remote-file.ps1' -Repo $repoShort -Branch $br -Path $p -Out $local | Out-Null

    if (-not (Test-Path $local)) { continue }

    $orig = [System.IO.File]::ReadAllText($local, [System.Text.Encoding]::UTF8)

    $t = $orig



    # cancel superseded runs instead of queueing them (faster feedback, still no cost limit)

    $t = $t -replace 'cancel-in-progress:\s*false', 'cancel-in-progress: true'

    # parity matrix: run linux+windows concurrently

    $t = $t -replace 'max-parallel:\s*1', 'max-parallel: 2'

    # large native artifacts: fastest compression

    $t = $t -replace 'compression-level:\s*6', 'compression-level: 1'



    # setup-java cache where absent within the next few lines

    $lines = $t -split "`n"

    for ($i=0; $i -lt $lines.Count; $i++) {

      if ($lines[$i] -match 'uses:\s*actions/setup-java@') {

        $indent = ''

        if ($lines[$i] -match '^(\s*)') { $indent = $Matches[1] }

        $hasCache = $false

        for ($j=$i+1; $j -lt [Math]::Min($i+8,$lines.Count); $j++) {

          if ($lines[$j] -match '^\s*cache:') { $hasCache = $true; break }

          if ($lines[$j] -match '^\S') { break }

        }

        if (-not $hasCache) {

          $newLines = @()

          for ($k=0; $k -le $i; $k++) { $newLines += $lines[$k] }

          $newLines += ($indent + '  cache: maven')

          for ($k=$i+1; $k -lt $lines.Count; $k++) { $newLines += $lines[$k] }

          $lines = $newLines

          $i++

        }

      }

    }

    $t = ($lines -join "`n")



    if ($t -ne $orig) {

      [System.IO.File]::WriteAllText($local, $t, [System.Text.UTF8Encoding]::new($false))

      & 'D:\work\runtime-logs\put-remote-file.ps1' -Repo $RepoFull -Branch $br -Path $p -Src $local -Message 'ci(perf): cancel stale runs, parallel parity, faster artifacts, Maven cache' | Out-Null

      Write-Output "OPT $br/$p"

      $changedCount++

    }

    Remove-Item $local -Force -ErrorAction SilentlyContinue

  }

}

Write-Output "CHANGED_FILES=$changedCount"

