# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 重建并重启 api（Spring Boot 4.1.2 / JDK 17），用于实机联调迭代
param(
    [switch]$SkipBuild,
    [int]$WaitSeconds = 60
)
$ErrorActionPreference = 'Stop'
$logDir = 'D:\work\runtime-logs'
$logFile = Join-Path $logDir 'api-jdk17-sb4.log'

$conns = Get-NetTCPConnection -State Listen -LocalPort 9902 -ErrorAction SilentlyContinue
foreach ($c in $conns) {
    Write-Host "stopping PID $($c.OwningProcess) on 9902"
    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
}
Get-CimInstance Win32_Process -Filter "Name='java.exe'" | Where-Object { $_.CommandLine -like '*car-monit-api-jdk17*' } | ForEach-Object {
    Write-Host "stopping stale api java PID $($_.ProcessId)"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2

if (-not $SkipBuild) {
    $env:JAVA_HOME = 'D:\jdk\temurin-17\jdk-17.0.21+9'
    $env:MAVEN_OPTS = '-Duser.language=en -Duser.country=US'
    Push-Location 'D:\work\IdeaProjects\car-monit-api-jdk17'
    & 'D:\work\apache-maven\bin\mvn.cmd' -B -DskipTests -q package 2>&1 |
        Select-String -Pattern 'ERROR' | Select-Object -First 20
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw 'maven package failed' }
    Pop-Location
}

& (Join-Path $logDir 'start-api-jdk17-sb4.ps1') | Out-Null
Start-Sleep -Seconds $WaitSeconds

$ok = Get-NetTCPConnection -State Listen -LocalPort 9902 -ErrorAction SilentlyContinue
if ($ok) {
    Write-Host "API UP on 9902 (PID $($ok.OwningProcess))"
} else {
    Write-Host 'API NOT LISTENING - last log:'
    Get-Content $logFile -Tail 60 -Encoding UTF8
}
