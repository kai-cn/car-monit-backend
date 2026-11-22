# @description 历史脚本 watchdog_v4.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage powershell -File watchdog_v4.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Long-running monitor for GitHub Actions status.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

$log="D:\work\runtime-logs\watchdog-v4.log"

$base="D:\work\runtime-logs\gh_api.ps1"

$targets=@(

  @{repo='kai-cn/car-monit-api';id=43908450970;label='API master dispatch final'},

  @{repo='kai-cn/car-monit-api';id=43908459793;label='API pr dispatch final'},

  @{repo='kai-cn/car-monit-api';id=43908432856;label='API master push final'},

  @{repo='kai-cn/car-monit-backend';id=43908208183;label='BACKEND ci dispatch final'}

)

function W($m){("{0} {1}" -f (Get-Date -Format HH:mm:ss),$m)|Out-File -FilePath $log -Append -Encoding utf8}

"=== WATCHDOG V4 START ===" | Out-File -FilePath $log -Encoding utf8

$deadline=(Get-Date).AddMinutes(60); $done=$false

while((Get-Date) -lt $deadline){

  $all=$true; $parts=@()

  foreach($t in $targets){

    $o=& $base -Method GET -Uri "https://api.github.com/repos/$($t.repo)/actions/runs/$($t.id)"|ConvertFrom-Json

    $parts += ("{0}={1}/{2}" -f $t.label,$o.status,$o.conclusion)

    if($o.status -ne 'completed'){$all=$false}

  }

  W ($parts -join ' | ')

  if($all){$done=$true;break}

  Start-Sleep -Seconds 30

}

if($done){

  W "ALL FINAL RUNS DONE"

  $bf=Join-Path $env:TEMP 'pv4a.json'; [System.IO.File]::WriteAllText($bf,'{"private":true}')

  & $base -Method PATCH -Uri "https://api.github.com/repos/kai-cn/car-monit-api" -BodyFile $bf|Out-Null; Remove-Item $bf -Force

  W "api -> private"

  $bf=Join-Path $env:TEMP 'pv4b.json'; [System.IO.File]::WriteAllText($bf,'{"private":true}')

  & $base -Method PATCH -Uri "https://api.github.com/repos/kai-cn/car-monit-backend" -BodyFile $bf|Out-Null; Remove-Item $bf -Force

  W "backend -> private"

  W "WATCHDOG V4 DONE"

} else { W "TIMEOUT - STILL PUBLIC" }

