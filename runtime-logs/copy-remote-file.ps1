# Copy one file between branches of the same repository through the GitHub API.
# Usage: copy-remote-file.ps1 -Repo <short-repo> -SrcBranch <branch> -DstBranch <branch> -Path <repo-path>
# Binary-safe: the file is fetched to a temp file and PUT as base64 (needed for .gz fixtures).
param(
  [Parameter(Mandatory=$true)][string]$Repo,
  [Parameter(Mandatory=$true)][string]$SrcBranch,
  [Parameter(Mandatory=$true)][string]$DstBranch,
  [Parameter(Mandatory=$true)][string]$Path,
  [string]$Message = 'chore(parity): deploy harness'
)
$tmp = Join-Path $env:TEMP "copyremote_$PID.bin"
& 'D:\work\runtime-logs\fetch-remote-file.ps1' -Repo $Repo -Branch $SrcBranch -Path $Path -Out $tmp | Out-Null
& 'D:\work\runtime-logs\put-remote-file.ps1' -Repo "kai-cn/$Repo" -Branch $DstBranch -Path $Path -Src $tmp -Message $Message | Select-String '"message"|HTTP_ERROR' | Select-Object -First 2
Remove-Item $tmp -Force -ErrorAction SilentlyContinue
