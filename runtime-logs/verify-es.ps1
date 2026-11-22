# @description 历史脚本 verify-es.ps1：验证配置、构建或安全不变量；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage powershell -File verify-es.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
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
