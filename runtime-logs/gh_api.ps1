# @description 历史脚本 gh_api.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage powershell -File gh_api.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

param(

  [Parameter(Mandatory=$true)][string]$Method,

  [Parameter(Mandatory=$true)][string]$Uri,

  [string]$BodyFile

)

$ErrorActionPreference='Stop'

# Use the cached credential bound to the fixed GitHub account (kai-cn).

# gh_cred.py calls `git credential fill` only on cache miss and passes username,

# so GCM never shows the account-picker dialog on every API call.

$tok = & python -c "import sys; sys.path.insert(0, r'D:\work\runtime-logs'); import gh_cred; sys.stdout.write(gh_cred.get_token())"

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($tok)) {

  Write-Output 'ERROR :: cannot read cached GitHub token (run: python D:\work\runtime-logs\gh_cred.py)'

  exit 1

}

$h=@{Authorization="Bearer $tok"; Accept='application/vnd.github+json'; 'X-GitHub-Api-Version'='2022-11-28'; 'User-Agent'='carmonit-audit'}

$args=@{Method=$Method; Uri=$Uri; Headers=$h; TimeoutSec=40}

if($BodyFile -and (Test-Path $BodyFile)){ $args.Body=[System.IO.File]::ReadAllText($BodyFile); $args.ContentType='application/json' }

try {

  $r=Invoke-RestMethod @args

  $r | ConvertTo-Json -Depth 20

} catch {

  $resp=$_.Exception.Response

  if($resp){ $sr=New-Object System.IO.StreamReader($resp.GetResponseStream()); $body=$sr.ReadToEnd(); Write-Output ("HTTP_ERROR status={0} :: {1}" -f [int]$resp.StatusCode, $body) }

  else { Write-Output ("ERROR :: " + $_.Exception.Message) }

}

