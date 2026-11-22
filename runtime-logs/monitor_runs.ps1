# @description 历史脚本 monitor_runs.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage powershell -File monitor_runs.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
param([Parameter(Mandatory=$true)][string]$Repo,[long[]]$Ids)
$base="D:\work\runtime-logs\gh_api.ps1"
foreach($id in $Ids){
  $json=& $base -Method GET -Uri "https://api.github.com/repos/$Repo/actions/runs/$id"
  try{$o=$json|ConvertFrom-Json}catch{Write-Output "$id PARSE_ERR";continue}
  Write-Output ("{0} | {1} | {2} | {3}" -f $id,$o.name,$o.status,$o.conclusion)
  if($o.status -eq 'in_progress'){
    $jobs=& $base -Method GET -Uri "https://api.github.com/repos/$Repo/actions/runs/$id/jobs?per_page=20"|ConvertFrom-Json
    foreach($j in $jobs.jobs){ Write-Output ("    {0}: {1}/{2}" -f $j.name,$j.status,$j.conclusion) }
  }
}
