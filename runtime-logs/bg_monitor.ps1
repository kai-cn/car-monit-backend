# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Background wrapper for a long-running monitor/build.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Background monitor: polls all active CICD runs and appends status to a log file.
$log = "D:\work\runtime-logs\cicd-test-progress.log"
$base = "D:\work\runtime-logs\gh_api.ps1"
$targets = @(
  @{repo='kai-cn/car-monit-api'; id=43900535384; label='API native jdk25 BUILD'},
  @{repo='kai-cn/car-monit-api'; id=43900652117; label='API master CICD'},
  @{repo='kai-cn/car-monit-api'; id=43900733283; label='API pr CICD'},
  @{repo='kai-cn/car-monit-backend'; id=43900593871; label='BACKEND native jdk25 BUILD'},
  @{repo='kai-cn/car-monit-backend'; id=43901010414; label='BACKEND ci CICD'}
)
$deadline = (Get-Date).AddMinutes(60)
while ((Get-Date) -lt $deadline) {
  $ts = Get-Date -Format 'HH:mm:ss'
  $lines = @("===== $ts =====")
  $allDone = $true
  foreach ($t in $targets) {
    $json = & $base -Method GET -Uri "https://api.github.com/repos/$($t.repo)/actions/runs/$($t.id)"
    try { $o = $json | ConvertFrom-Json } catch { $lines += "$($t.label): PARSE_ERR"; $allDone=$false; continue }
    $lines += ("{0}: status={1} conclusion={2}" -f $t.label, $o.status, $o.conclusion)
    if ($o.status -ne 'completed') { $allDone = $false }
  }
  $lines | Out-File -FilePath $log -Append -Encoding utf8
  if ($allDone) { "ALL_DONE at $ts" | Out-File -FilePath $log -Append -Encoding utf8; break }
  Start-Sleep -Seconds 30
}
