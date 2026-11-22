# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only verification of a security or build invariant.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
$HT = @{ 'X-Internal-Token' = 'local-dev-internal-token-0123456789' }
$urls = @(
  'pageNum=1&pageSize=5&applyTime1=2025-11-01&applyTime2=2025-11-30',
  'pageNum=1&pageSize=3&applyTime1=2025-11-14&applyTime2=2025-11-14',
  'pageNum=1&pageSize=3&platenumber=CBB'
)
foreach ($q in $urls) {
  $u = 'http://127.0.0.1:9902/base/snapshotflow/list?' + $q
  try {
    $x = Invoke-WebRequest -Uri $u -Headers $HT -UseBasicParsing -TimeoutSec 40
    $j = $x.Content | ConvertFrom-Json
    $plate = ''
    $tm = ''
    if ($j.rows -and $j.rows.Count -gt 0) { $plate = $j.rows[0].platenumber; $tm = $j.rows[0].snapshottimeStr }
    "{0} -> code={1} total={2} rows={3} plate={4} time={5}" -f $q, $j.code, $j.total, $j.rows.Count, $plate, $tm
  } catch {
    "{0} -> ERR {1}" -f $q, $_.Exception.Message
  }
}
