# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
param([Parameter(Mandatory=$true)][string]$Repo,[Parameter(Mandatory=$true)][long]$RunId,[switch]$Logs)
$base="D:\work\runtime-logs\gh_api.ps1"
$json = & $base -Method GET -Uri "https://api.github.com/repos/$Repo/actions/runs/$RunId/jobs?per_page=50"
try { $obj = $json | ConvertFrom-Json } catch { Write-Output "PARSE ERR"; Write-Output ($json | Select-Object -First 5); exit }
foreach($j in $obj.jobs){
  Write-Output ("JOB {0} | {1} | {2} | conclusion={3}" -f $j.id,$j.name,$j.status,$j.conclusion)
  if($Logs -and $j.conclusion -eq 'failure'){
    $lj = & $base -Method GET -Uri "https://api.github.com/repos/$Repo/actions/jobs/$($j.id)/logs"
    $lj | Select-String -Pattern 'error|Error|ERROR|fatal|Failed|failed|denied|not found|No such|Build FAILED|status' | Select-Object -Last 25 | ForEach-Object { Write-Output ("   " + $_.Line) }
  }
}
