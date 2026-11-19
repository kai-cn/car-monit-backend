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
