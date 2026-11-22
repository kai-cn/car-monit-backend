# @description 历史脚本 final-wsl-evidence.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage powershell -File final-wsl-evidence.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Purpose: copy WSL local retest evidence to D drive and print summaries.

# Idea: read WSL ext4 evidence via UNC, copy small JSON/log files to runtime-logs, then report counts.

# Risk: read-only from WSL; writes only local evidence files.

$src='\\wsl$\openEuler-24.03-LTS-SP4\home\dev\local-retest'

$dst='D:\work\runtime-logs\wsl-retest-evidence'

New-Item -ItemType Directory -Force -Path $dst | Out-Null

foreach($f in @('junit-contract.json','junit-load.json','contract.log','load.log','app.log')){

  $p=Join-Path $src $f

  if(Test-Path $p){ Copy-Item $p (Join-Path $dst $f) -Force }

}

$contract=Get-Content (Join-Path $dst 'junit-contract.json') -Raw -Encoding utf8 | ConvertFrom-Json

$load=Get-Content (Join-Path $dst 'junit-load.json') -Raw -Encoding utf8 | ConvertFrom-Json

Write-Output "ENDPOINTS=$($contract.endpoints.Count)"

Write-Output "LOAD total=$($load.total_requests) ok=$($load.ok) errors=$($load.errors) 4xx=$($load.business_4xx) 5xx=$($load.business_5xx) rps=$($load.rps) p95=$($load.p95_ms)"

Select-String -Path (Join-Path $dst 'contract.log') -Pattern 'tests successful|tests failed' | ForEach-Object { $_.Line.Trim() }

Select-String -Path (Join-Path $dst 'load.log') -Pattern 'tests successful|tests failed' | ForEach-Object { $_.Line.Trim() }

