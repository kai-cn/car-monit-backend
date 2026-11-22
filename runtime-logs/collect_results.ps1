# @description 历史脚本 collect_results.ps1：收集云端 run、job 或 artifact 状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage powershell -File collect_results.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Collect run results into a concise report.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# Collect final conclusions of all fixed-commit runs into one JSON-ish log file.

$out = "D:\work\runtime-logs\cicd-final-results.txt"

$base = "D:\work\runtime-logs\gh_api.ps1"

$targets = @(

  @{repo='kai-cn/car-monit-api'; id=43904553508; label='API native BUILD'},

  @{repo='kai-cn/car-monit-api'; id=43904462076; label='API master dispatch'},

  @{repo='kai-cn/car-monit-api'; id=43904470791; label='API pr dispatch'},

  @{repo='kai-cn/car-monit-api'; id=43904404314; label='API master push'},

  @{repo='kai-cn/car-monit-backend'; id=43904489086; label='BACKEND native BUILD'},

  @{repo='kai-cn/car-monit-backend'; id=43904480854; label='BACKEND ci dispatch'}

)

function W($m){ ("{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m) | Out-File -FilePath $out -Append -Encoding utf8 }

"===== RESULT COLLECTOR START =====" | Out-File -FilePath $out -Encoding utf8

$deadline = (Get-Date).AddMinutes(90)

$done = $false

while ((Get-Date) -lt $deadline) {

  $allDone = $true

  foreach ($t in $targets) {

    $rj = & $base -Method GET -Uri "https://api.github.com/repos/$($t.repo)/actions/runs/$($t.id)" | ConvertFrom-Json

    if ($rj.status -ne 'completed') { $allDone = $false; continue }

  }

  if ($allDone) { $done = $true; break }

  Start-Sleep -Seconds 30

}

if (-not $done) { W "TIMEOUT"; exit }

foreach ($t in $targets) {

  $rj = & $base -Method GET -Uri "https://api.github.com/repos/$($t.repo)/actions/runs/$($t.id)" | ConvertFrom-Json

  W ("RUN {0} id={1} sha={2} STATUS={3} CONCLUSION={4}" -f $t.label,$t.id,$rj.head_sha.Substring(0,7),$rj.status,$rj.conclusion)

  $jj = & $base -Method GET -Uri "https://api.github.com/repos/$($t.repo)/actions/runs/$($t.id)/jobs?per_page=30" | ConvertFrom-Json

  foreach ($j in $jj.jobs) { W ("   JOB {0} -> {1}" -f $j.name,$j.conclusion) }

}

W "===== ALL RESULTS COLLECTED ====="

