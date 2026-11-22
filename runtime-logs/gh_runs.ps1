# @description 历史脚本 gh_runs.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage powershell -File gh_runs.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
param([Parameter(Mandatory=$true)][string]$Repo,[int]$PerPage=8)
$base="D:\work\runtime-logs\gh_api.ps1"
$json = & $base -Method GET -Uri "https://api.github.com/repos/$Repo/actions/runs?per_page=$PerPage"
try { $obj = $json | ConvertFrom-Json } catch { Write-Output "PARSE ERR"; Write-Output ($json | Select-Object -First 3); exit }
foreach($r in $obj.workflow_runs){
  Write-Output ("{0} | {1} | {2} | evt={3} | branch={4} | sha={5} | {6}" -f $r.id,$r.name,$r.status,$r.event,$r.head_branch,$r.head_sha.Substring(0,7),$r.conclusion)
}
