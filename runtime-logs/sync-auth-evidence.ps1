# @description 将 WSL 本机鉴权复测证据复制到 backend master runtime-logs 并生成轻量摘要。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage powershell -File runtime-logs/sync-auth-evidence.ps1
# @dependencies WSL ext4 中 /home/dev/local-auth-retest 证据。
$src = '\\wsl$\openEuler-24.03-LTS-SP4\home\dev\local-auth-retest'
$dst = 'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs\wsl-retest-auth'
New-Item -ItemType Directory -Force -Path $dst | Out-Null
foreach ($name in @('junit-contract.json', 'junit-load.json', 'contract.log', 'load.log', 'app.log')) {
    if (Test-Path (Join-Path $src $name)) { Copy-Item (Join-Path $src $name) (Join-Path $dst $name) -Force }
}
$contract = Get-Content (Join-Path $dst 'junit-contract.json') -Raw -Encoding utf8 | ConvertFrom-Json
$load = Get-Content (Join-Path $dst 'junit-load.json') -Raw -Encoding utf8 | ConvertFrom-Json
$authFail = @($contract.endpoints | Where-Object { $_.body -match '认证失败' }).Count
$lines = @(
    '# WSL 本机管理员鉴权复测证据',
    '',
    "- endpoints: $($contract.endpoint_count)",
    "- auth_fail: $authFail",
    "- load_total: $($load.total_requests)",
    "- load_ok: $($load.ok)",
    "- load_errors: $($load.errors)",
    "- business_4xx: $($load.business_4xx)",
    "- business_5xx: $($load.business_5xx)",
    "- rps: $([math]::Round($load.rps,2))",
    ''
)
$evidencePath = Join-Path $dst 'evidence.md'
$lines | Set-Content -Path $evidencePath -Encoding utf8
$lines
