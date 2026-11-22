# @description 历史脚本 annotate-workflows-cloud.ps1：批量补充脚本或代码注释；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage powershell -File annotate-workflows-cloud.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Maven 与对应 JDK
# LEGACY-SCRIPT-ANNOTATION

# 文件：annotate-workflows-cloud.ps1

# 用途：批量补充脚本注释。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：会修改本地脚本文件，执行前确认目录。

param([Parameter(Mandatory=$true)][string]$RepoFull)

# Add explanatory comments next to the performance options injected earlier.

# Usage: annotate-workflows-cloud.ps1 -RepoFull <owner/repo>

# Safe/idempotent: skips a line when its comment already appears within the previous 3 lines.

$repoShort = $RepoFull.Split('/')[-1]

$tmp = Join-Path $env:TEMP "wfannot_$repoShort"

New-Item -ItemType Directory -Force -Path $tmp | Out-Null

function Api([string]$uri){ (& 'D:\work\runtime-logs\gh_api.ps1' -Method GET -Uri $uri | Out-String) }

$raw = Api "https://api.github.com/repos/$RepoFull/branches?per_page=100"

$branches = @([regex]::Matches($raw,'"name":\s+"([^"]+)"') | ForEach-Object { $_.Groups[1].Value })

$changed = 0



$RULES = @(

  @{ pattern='cancel-in-progress:\s*true'; comment='Perf: cancel superseded runs so the queue always serves the newest commit.' },

  @{ pattern='max-parallel:\s*2'; comment='Perf: matrix cells use separate cloud runners; run them concurrently.' },

  @{ pattern='compression-level:\s*1'; comment='Perf: large native artifacts use fast compression; integrity is covered by sha256.' },

  @{ pattern='-\s*name:\s*Cache Maven repository'; comment='Perf: reuse ~/.m2/repository across runs; key follows pom.xml changes.' },

  @{ pattern='cache:\s*maven'; comment='Perf: let setup-java restore Maven dependencies from the action cache.' }

)



foreach ($br in $branches) {

  $enc = [uri]::EscapeDataString($br)

  $wf = Api "https://api.github.com/repos/$RepoFull/contents/.github/workflows?ref=$enc"

  $paths = @([regex]::Matches($wf,'"path":\s+"([^"]+\.ya?ml)"') | ForEach-Object { $_.Groups[1].Value })

  foreach ($p in $paths) {

    $local = Join-Path $tmp ("f_" + [guid]::NewGuid().ToString('N') + ".yml")

    & 'D:\work\runtime-logs\fetch-remote-file.ps1' -Repo $repoShort -Branch $br -Path $p -Out $local | Out-Null

    if (-not (Test-Path $local)) { continue }

    $orig = [System.IO.File]::ReadAllText($local, [System.Text.Encoding]::UTF8)

    $lines = $orig -split "`n"

    $out = @()

    $touched = $false

    for ($i=0; $i -lt $lines.Count; $i++) {

      $line = $lines[$i]

      $matchedRule = $null

      foreach ($r in $RULES) { if ($line -match $r.pattern) { $matchedRule = $r; break } }

      if ($matchedRule) {

        $hasComment = $false

        for ($j=[Math]::Max(0,$i-3); $j -lt $i; $j++) {

          if ($lines[$j] -like "*$($matchedRule.comment)*") { $hasComment = $true; break }

        }

        if (-not $hasComment) {

          $indent = ''

          if ($line -match '^(\s*)') { $indent = $Matches[1] }

          $out += ($indent + '# ' + $matchedRule.comment)

          $touched = $true

        }

      }

      $out += $line

    }

    if ($touched) {

      $t = $out -join "`n"

      [System.IO.File]::WriteAllText($local, $t, [System.Text.UTF8Encoding]::new($false))

      & 'D:\work\runtime-logs\put-remote-file.ps1' -Repo $RepoFull -Branch $br -Path $p -Src $local -Message 'ci(comment): explain performance workflow options' | Out-Null

      Write-Output "ANNOT $br/$p"

      $changed++

    }

    Remove-Item $local -Force -ErrorAction SilentlyContinue

  }

}

Write-Output "ANNOTATED_FILES=$changed"

