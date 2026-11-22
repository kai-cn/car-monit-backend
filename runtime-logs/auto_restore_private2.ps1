# @description 历史脚本 auto_restore_private2.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage powershell -File auto_restore_private2.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Automation helper created during the public-repo CICD session; inspect before running.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Watchdog v2: wait for the fixed-commit CICD runs, then restore both repos to PRIVATE.

$log = "D:\work\runtime-logs\auto-restore-private2.log"

$base = "D:\work\runtime-logs\gh_api.ps1"

$targets = @(

  @{repo='kai-cn/car-monit-api'; id=43904553508; label='API native jdk25 BUILD (fixed)'},

  @{repo='kai-cn/car-monit-api'; id=43904462076; label='API master dispatch (fixed)'},

  @{repo='kai-cn/car-monit-api'; id=43904470791; label='API pr dispatch (fixed)'},

  @{repo='kai-cn/car-monit-api'; id=43904404314; label='API master push (fixed)'},

  @{repo='kai-cn/car-monit-backend'; id=43904489086; label='BACKEND native jdk25 BUILD (fixed)'},

  @{repo='kai-cn/car-monit-backend'; id=43904480854; label='BACKEND ci dispatch (fixed)'}

)

function Log($m){ ("{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) | Out-File -FilePath $log -Append -Encoding utf8 }

Log "WATCHDOG V2 START - waiting for fixed-commit runs"

$deadline = (Get-Date).AddMinutes(90)

$done = $false

while ((Get-Date) -lt $deadline) {

  $allDone = $true

  $summary = @()

  foreach ($t in $targets) {

    $json = & $base -Method GET -Uri "https://api.github.com/repos/$($t.repo)/actions/runs/$($t.id)"

    try { $o = $json | ConvertFrom-Json } catch { $allDone = $false; continue }

    $summary += ("{0}={1}/{2}" -f $t.label, $o.status, $o.conclusion)

    if ($o.status -ne 'completed') { $allDone = $false }

  }

  Log ("CHECK " + ($summary -join ' | '))

  if ($allDone) { $done = $true; break }

  Start-Sleep -Seconds 30

}

if ($done) {

  Log "ALL FIXED RUNS COMPLETE - restoring private"

  $bf = Join-Path $env:TEMP 'pv1.json'; [System.IO.File]::WriteAllText($bf,'{"private":true}')

  & $base -Method PATCH -Uri "https://api.github.com/repos/kai-cn/car-monit-api" -BodyFile $bf | Out-Null

  Remove-Item $bf -Force -ErrorAction SilentlyContinue

  Log "api -> private"

  $bf = Join-Path $env:TEMP 'pv2.json'; [System.IO.File]::WriteAllText($bf,'{"private":true}')

  & $base -Method PATCH -Uri "https://api.github.com/repos/kai-cn/car-monit-backend" -BodyFile $bf | Out-Null

  Remove-Item $bf -Force -ErrorAction SilentlyContinue

  Log "backend -> private"

  Log "WATCHDOG V2 DONE"

} else {

  Log "TIMEOUT - repos STILL PUBLIC - MANUAL ACTION REQUIRED"

}

