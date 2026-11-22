# @description 历史脚本 auto_restore_private3.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage powershell -File auto_restore_private3.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Automation helper created during the public-repo CICD session; inspect before running.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Watchdog v3: final fixed-commit runs, then restore both repos to PRIVATE.

$log = "D:\work\runtime-logs\auto-restore-private3.log"

$base = "D:\work\runtime-logs\gh_api.ps1"

$targets = @(

  @{repo='kai-cn/car-monit-api'; id=43905084757; label='API native BUILD (ade6c80)'},

  @{repo='kai-cn/car-monit-api'; id=43905468152; label='API master (60cfc5e)'},

  @{repo='kai-cn/car-monit-api'; id=43905476617; label='API pr (60cfc5e)'},

  @{repo='kai-cn/car-monit-backend'; id=43905459051; label='BACKEND native BUILD (76c133f)'},

  @{repo='kai-cn/car-monit-backend'; id=43904480854; label='BACKEND ci (434ac71)'}

)

function Log($m){ ("{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) | Out-File -FilePath $log -Append -Encoding utf8 }

Log "WATCHDOG V3 START"

$deadline = (Get-Date).AddMinutes(90)

$done = $false

while ((Get-Date) -lt $deadline) {

  $allDone = $true

  foreach ($t in $targets) {

    $o = & $base -Method GET -Uri "https://api.github.com/repos/$($t.repo)/actions/runs/$($t.id)" | ConvertFrom-Json

    if ($o.status -ne 'completed') { $allDone = $false; break }

  }

  if ($allDone) { $done = $true; break }

  Start-Sleep -Seconds 30

}

if ($done) {

  Log "ALL FINAL RUNS COMPLETE - restoring private"

  $bf = Join-Path $env:TEMP 'pv3a.json'; [System.IO.File]::WriteAllText($bf,'{"private":true}')

  & $base -Method PATCH -Uri "https://api.github.com/repos/kai-cn/car-monit-api" -BodyFile $bf | Out-Null

  Remove-Item $bf -Force

  Log "api -> private"

  $bf = Join-Path $env:TEMP 'pv3b.json'; [System.IO.File]::WriteAllText($bf,'{"private":true}')

  & $base -Method PATCH -Uri "https://api.github.com/repos/kai-cn/car-monit-backend" -BodyFile $bf | Out-Null

  Remove-Item $bf -Force

  Log "backend -> private"

  Log "WATCHDOG V3 DONE"

} else { Log "TIMEOUT - repos STILL PUBLIC - MANUAL ACTION REQUIRED" }

