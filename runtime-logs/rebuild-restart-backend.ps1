# @description 历史脚本 rebuild-restart-backend.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage powershell -File rebuild-restart-backend.ps1 [params]；参数含义见脚本原有注释。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 重建并重启 backend（Spring Boot 4.1.2 / JDK 17），用于实机联调迭代

param(

    [switch]$SkipBuild,

    [int]$WaitSeconds = 60

)

$ErrorActionPreference = 'Stop'

$logDir = 'D:\work\runtime-logs'

$logFile = Join-Path $logDir 'backend-jdk17-sb4.log'



# 1. 停掉占用 9989 的实例 / 正在跑本 jar 的 java 进程

$conns = Get-NetTCPConnection -State Listen -LocalPort 9989 -ErrorAction SilentlyContinue

foreach ($c in $conns) {

    Write-Host "stopping PID $($c.OwningProcess) on 9989"

    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue

}

Get-CimInstance Win32_Process -Filter "Name='java.exe'" | Where-Object { $_.CommandLine -like '*car-monit-backend-jdk17*' } | ForEach-Object {

    Write-Host "stopping stale backend java PID $($_.ProcessId)"

    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue

}

Start-Sleep -Seconds 2



# 2. 构建

if (-not $SkipBuild) {

    $env:JAVA_HOME = 'D:\jdk\temurin-17\jdk-17.0.21+9'

    $env:MAVEN_OPTS = '-Duser.language=en -Duser.country=US'

    Push-Location 'D:\work\IdeaProjects\car-monit-backend-jdk17'

    & 'D:\work\apache-maven\bin\mvn.cmd' -B -DskipTests -q package 2>&1 |

        Select-String -Pattern 'ERROR' | Select-Object -First 20

    if ($LASTEXITCODE -ne 0) { Pop-Location; throw 'maven package failed' }

    Pop-Location

}



# 3. 启动

& (Join-Path $logDir 'start-backend-jdk17-sb4.ps1') | Out-Null

Start-Sleep -Seconds $WaitSeconds



$ok = Get-NetTCPConnection -State Listen -LocalPort 9989 -ErrorAction SilentlyContinue

if ($ok) {

    Write-Host "BACKEND UP on 9989 (PID $($ok.OwningProcess))"

} else {

    Write-Host 'BACKEND NOT LISTENING - last log:'

    Get-Content $logFile -Tail 40

}

