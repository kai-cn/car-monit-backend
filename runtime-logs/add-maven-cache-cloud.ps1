# LEGACY-SCRIPT-ANNOTATION
# 文件：add-maven-cache-cloud.ps1
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
# Add an explicit ~/.m2/repository cache step to Maven-based workflows that lack one.
# Usage: add-maven-cache-cloud.ps1 -RepoFull <owner/repo>
# Skips workflows already using actions/cache or setup-java cache: maven.
# Cache key uses hashFiles('**/pom.xml'), restoring the latest compatible dependency cache.
param([Parameter(Mandatory=$true)][string]$RepoFull)
$repoShort = $RepoFull.Split('/')[-1]
$tmp = Join-Path $env:TEMP "m2cache_$repoShort"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
function Api([string]$uri){ (& 'D:\work\runtime-logs\gh_api.ps1' -Method GET -Uri $uri | Out-String) }
$raw = Api "https://api.github.com/repos/$RepoFull/branches?per_page=100"
$branches = @([regex]::Matches($raw,'"name":\s+"([^"]+)"') | ForEach-Object { $_.Groups[1].Value })
$changed = 0
foreach ($br in $branches) {
  $enc = [uri]::EscapeDataString($br)
  $wf = Api "https://api.github.com/repos/$RepoFull/contents/.github/workflows?ref=$enc"
  $paths = @([regex]::Matches($wf,'"path":\s+"([^"]+\.ya?ml)"') | ForEach-Object { $_.Groups[1].Value })
  foreach ($p in $paths) {
    $local = Join-Path $tmp ("f_" + [guid]::NewGuid().ToString('N') + ".yml")
    & 'D:\work\runtime-logs\fetch-remote-file.ps1' -Repo $repoShort -Branch $br -Path $p -Out $local | Out-Null
    if (-not (Test-Path $local)) { continue }
    $orig = [System.IO.File]::ReadAllText($local, [System.Text.Encoding]::UTF8)
    if ($orig -notmatch '(?m)^\s*(mvn|"\$MVN"|mvn\.cmd)' -or $orig -match 'actions/cache@' -or $orig -match 'cache:\s*maven') {
      Remove-Item $local -Force; continue
    }
    $lines = $orig -split "`n"
    $idx = -1; $indent = ''
    for ($i=0; $i -lt $lines.Count; $i++) {
      if ($lines[$i] -match '^(\s*)-\s*uses:\s*actions/checkout@') { $idx=$i; $indent=$Matches[1]; break }
    }
    if ($idx -lt 0) { Remove-Item $local -Force; continue }
    $block = @(
      ($indent + '- name: Cache Maven repository'),
      ($indent + '  uses: actions/cache@v4'),
      ($indent + '  with:'),
      ($indent + '    path: ~/.m2/repository'),
      ($indent + '    key: ${{ runner.os }}-m2-${{ hashFiles(''**/pom.xml'') }}'),
      ($indent + '    restore-keys: ${{ runner.os }}-m2-')
    )
    $out=@()
    for ($i=0; $i -le $idx; $i++) { $out += $lines[$i] }
    $out += $block
    for ($i=$idx+1; $i -lt $lines.Count; $i++) { $out += $lines[$i] }
    $t = $out -join "`n"
    [System.IO.File]::WriteAllText($local, $t, [System.Text.UTF8Encoding]::new($false))
    & 'D:\work\runtime-logs\put-remote-file.ps1' -Repo $RepoFull -Branch $br -Path $p -Src $local -Message 'ci(perf): cache Maven repository forJava workflows' | Out-Null
    Write-Output "CACHE $br/$p"
    $changed++
    Remove-Item $local -Force
  }
}
Write-Output "CACHE_FILES=$changed"
