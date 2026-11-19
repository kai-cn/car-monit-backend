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
