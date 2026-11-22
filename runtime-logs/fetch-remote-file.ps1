# @description 历史脚本 fetch-remote-file.ps1：从远端读取文件或状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage powershell -File fetch-remote-file.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# LEGACY-SCRIPT-ANNOTATION

# 文件：fetch-remote-file.ps1

# 用途：同步或拉取本地/远端内容。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：可能更新本地工作树或读取远端，执行前确认目标分支。

# Fetch a single file from a remote GitHub branch via the REST contents API.

# Usage: fetch-remote-file.ps1 -Repo <short-repo> -Branch <branch> -Path <repo-path> -Out <local-file>

# Token is read from git credential helper by gh_api.ps1; never echoed or persisted.

param(

  [Parameter(Mandatory=$true)][string]$Repo,

  [Parameter(Mandatory=$true)][string]$Branch,

  [Parameter(Mandatory=$true)][string]$Path,

  [Parameter(Mandatory=$true)][string]$Out

)

$uri = "https://api.github.com/repos/kai-cn/$Repo/contents/$($Path -replace ' ','%20')?ref=$Branch"

$json = & 'D:\work\runtime-logs\gh_api.ps1' -Method GET -Uri $uri | Out-String

$obj = $json | ConvertFrom-Json

if ($null -eq $obj.content) { Write-Error "NO CONTENT $uri :: $json"; exit 1 }

[System.IO.File]::WriteAllBytes($Out, [Convert]::FromBase64String(($obj.content -replace '\s','')))

Write-Output "FETCHED $Repo/$Branch/$Path -> $Out $((Get-Item $Out).Length)"

