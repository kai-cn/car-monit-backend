# @description 历史脚本 auto_restore_private.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage powershell -File auto_restore_private.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Automation helper created during the public-repo CICD session; inspect before running.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Watchdog: waits for all CICD runs to complete, then restores both repos to PRIVATE (safety net).

$log = "D:\work\runtime-logs\auto-restore-private.log"

$base = "D:\work\runtime-logs\gh_api.ps1"

$targets = @(

  @{repo='kai-cn/car-monit-api'; id=43900535384},

  @{repo='kai-cn/car-monit-api'; id=43900652117},

  @{repo='kai-cn/car-monit-api'; id=43900733283},

  @{repo='kai-cn/car-monit-backend'; id=43900593871},

  @{repo='kai-cn/car-monit-backend'; id=43901010414}

)

function Log($m){ ("{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) | Out-File -FilePath $log -Append -Encoding utf8 }

Log "WATCHDOG START - will restore private when all runs complete"

$deadline = (Get-Date).AddMinutes(90)

$done = $false

while ((Get-Date) -lt $deadline) {

  $allDone = $true

  foreach ($t in $targets) {

    $json = & $base -Method GET -Uri "https://api.github.com/repos/$($t.repo)/actions/runs/$($t.id)"

    try { $o = $json | ConvertFrom-Json } catch { $allDone = $false; continue }

    if ($o.status -ne 'completed') { $allDone = $false }

  }

  if ($allDone) { Log "ALL RUNS COMPLETE - restoring private"; $done = $true; break }

  Start-Sleep -Seconds 30

}

if ($done) {

  $bf = Join-Path $env:TEMP 'priv_api.json'; [System.IO.File]::WriteAllText($bf,'{"private":true}')

  & $base -Method PATCH -Uri "https://api.github.com/repos/kai-cn/car-monit-api" -BodyFile $bf | Out-Null

  Remove-Item $bf -Force -ErrorAction SilentlyContinue

  Log "api repo -> private"

  $bf = Join-Path $env:TEMP 'priv_bk.json'; [System.IO.File]::WriteAllText($bf,'{"private":true}')

  & $base -Method PATCH -Uri "https://api.github.com/repos/kai-cn/car-monit-backend" -BodyFile $bf | Out-Null

  Remove-Item $bf -Force -ErrorAction SilentlyContinue

  Log "backend repo -> private"

  Log "WATCHDOG DONE"

} else {

  Log "WATCHDOG TIMEOUT (90min) - repos STILL PUBLIC - MANUAL ACTION REQUIRED"

}

