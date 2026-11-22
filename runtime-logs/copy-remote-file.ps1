# @description 历史脚本 copy-remote-file.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage powershell -File copy-remote-file.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# LEGACY-SCRIPT-ANNOTATION

# 文件：copy-remote-file.ps1

# 用途：同步或拉取本地/远端内容。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：可能更新本地工作树或读取远端，执行前确认目标分支。

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

