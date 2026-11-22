# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 启动 car-monit-backend (Spring Boot 4.1.2 / JDK 17) 的本地联调脚本
# 注意：凭据一律由运行环境注入，不要写死到仓库；本文件仅放在 D:\work\runtime-logs 下使用。
$ErrorActionPreference = 'Stop'

$env:JAVA_HOME = 'D:\jdk\temurin-17\jdk-17.0.21+9'
$java = Join-Path $env:JAVA_HOME 'bin\java.exe'
$jar  = 'D:\work\IdeaProjects\car-monit-backend-jdk17\ruoyi-admin\target\ruoyi-admin.jar'
$logDir = 'D:\work\runtime-logs'
$logFile = Join-Path $logDir 'backend-jdk17-sb4.log'

if (-not (Test-Path $jar)) { throw "jar not found: $jar" }

# 端口占用检查：避免重复启动第二个 backend
$busy = Get-NetTCPConnection -State Listen -LocalPort 9989 -ErrorAction SilentlyContinue
if ($busy) { throw "port 9989 already in use by PID $($busy.OwningProcess); stop it first" }

# 必需的环境变量（未注入时给本地联调默认值，仅用于本机验证）
if (-not $env:EXPORT_DOWNLOAD_SECRET) { $env:EXPORT_DOWNLOAD_SECRET = 'local-dev-export-download-secret-0123456789' }
if (-not $env:TRAFFIC_API_INTERNAL_TOKEN) { $env:TRAFFIC_API_INTERNAL_TOKEN = 'local-dev-internal-token-0123456789' }

$args = @(
  '-Xms512m', '-Xmx1024m',
  '-XX:+UseG1GC',
  '-Dfile.encoding=UTF-8',
  '-Duser.timezone=Asia/Shanghai',
  '-jar', $jar,
  '--server.port=9989'
)

Start-Process -FilePath $java -ArgumentList $args -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err" -NoNewWindow -PassThru |
  Select-Object Id,ProcessName
Write-Host "backend starting, log: $logFile"
