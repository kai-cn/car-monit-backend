# LEGACY-SCRIPT-ANNOTATION
# 文件：put-remote-file.ps1
# 用途：推送内容到远端。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：会修改远端分支，执行前确认凭据与目标。
# Create/update a single file on a remote GitHub branch via the REST contents API.
# Usage: put-remote-file.ps1 -Repo <owner/repo> -Branch <branch> -Path <repo-path> -Src <local-file> -Message <commit-msg>
# Reads the existing blob SHA when present so updates do not rewrite history; 404 means create new file.
param(
  [Parameter(Mandatory=$true)][string]$Repo,          # kai-cn/car-monit-api
  [Parameter(Mandatory=$true)][string]$Branch,
  [Parameter(Mandatory=$true)][string]$Path,
  [Parameter(Mandatory=$true)][string]$Src,
  [Parameter(Mandatory=$true)][string]$Message
)
$ErrorActionPreference='Stop'
$api="https://api.github.com/repos/$Repo/contents/$($Path -replace ' ','%20')"
Write-Output "API=$api BRANCH=$Branch"
$q = & 'D:\work\runtime-logs\gh_api.ps1' -Method GET -Uri "${api}?ref=${Branch}" | Out-String
if ($q -match 'HTTP_ERROR status=404') {
  $old = @{}
} else {
  try { $old = $q | ConvertFrom-Json } catch { Write-Output "GET DEBUG: $q"; throw }
}
$sha = if ($null -ne $old.sha) { $old.sha } else { $null }
$bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $Src))
$bodyObj = @{ message=$Message; branch=$Branch; content=[Convert]::ToBase64String($bytes); encoding='base64' }
if ($sha) { $bodyObj.sha = $sha }
$tmp = Join-Path $env:TEMP "putfile_$PID.json"
[System.IO.File]::WriteAllText($tmp, ($bodyObj | ConvertTo-Json -Depth 8 -Compress))
try {
  $r = & 'D:\work\runtime-logs\gh_api.ps1' -Method PUT -Uri $api -BodyFile $tmp | Out-String
  Write-Output $r
} finally { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
