<#
.SYNOPSIS
    car-monit V3 联调环境一键启动 / 状态 / 停止（backend + api + 中间件）。

.DESCRIPTION
    幂等：先按端口和进程命令行判断，服务已在跑就跳过，绝不重复启动第二个实例。
    顺序：openGauss(检查) -> MySQL8(检查) -> Redis -> Kafka -> ES -> api -> backend。
    约束：Windows 本机最多 1 个 backend java + 1 个 api java；ES/Kafka/Redis 各 1 个；
          MySQL8 只检查 3307 现有实例，不在其它 data 目录另起 mysqld。
    内存：默认 Low 档（java 各 768m、ES 512m、Kafka 512m），启动时打印宿主可用内存与预算。
    日志：D:\work\runtime-logs\v3-<name>.{out,err}.log；旧日志直接删除，不进回收站。
    凭据：不写入本文件。按 -EnvFile / 环境变量 / 既有 start-api-v3.ps1 顺序取值；
          内部端点令牌与下载签名密钥缺失时自动生成会话级随机值。

.PARAMETER Status        只查看状态，不启动
.PARAMETER Stop          仅停止由本脚本启动的进程（依据 v3-pids.json）
.PARAMETER Build         启动前先 mvn -o -DskipTests package 两侧 jar
.PARAMETER Minimal       不主动启动 ES / Kafka（仅检查端口；已跑则复用）
.PARAMETER SkipOpenGauss 跳过 openGauss 可达性检查
.PARAMETER SkipApi       不启动 api
.PARAMETER SkipBackend   不启动 backend
.PARAMETER MemoryProfile Low(默认) / Normal
.PARAMETER TimeoutSec    单个服务等待端口就绪的秒数
.PARAMETER EnvFile       可选本地环境脚本（放明文凭据，勿入库）

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\v3\start-v3-all.ps1 -Status
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\v3\start-v3-all.ps1 -Minimal
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\v3\start-v3-all.ps1 -Stop

.NOTES
    首次使用若 api 连不上 openGauss，请设置
      SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD
    或让 D:\work\runtime-logs\api-local.properties 非空（该值不入库）。
#>
[CmdletBinding()]
param(
    [switch]$Status,
    [switch]$Stop,
    [switch]$Build,
    [switch]$Minimal,
    [switch]$SkipOpenGauss,
    [switch]$SkipApi,
    [switch]$SkipBackend,
    [ValidateSet('Low', 'Normal')][string]$MemoryProfile = 'Low',
    [int]$TimeoutSec = 120,
    [string]$LogDir = 'D:\work\runtime-logs',
    [string]$EnvFile = 'D:\work\runtime-logs\v3-env.ps1'
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------- 配置
$Java8      = 'D:\jdk\jdk1.8.0_202\bin\java.exe'
$Java21Home = 'D:\jdk\temurin-21.0.12.1_1\jdk-21.0.12.1+1'
$BackendRoot = 'd:\work\IdeaProjects\car-monit-backend-java-V3'
$ApiRoot     = 'd:\work\IdeaProjects\car-monit-api-java-V3'
$BackendJar  = Join-Path $BackendRoot 'ruoyi-admin\target\ruoyi-admin.jar'
$ApiJar      = Join-Path $ApiRoot 'pro-business-api\target\pro-business-api-1.0.jar'
$EsHome      = 'D:\work\elasticsearch-7.15.2'
$KafkaHome   = 'D:\work\kafka_2.13-4.0.0'
$RedisHome   = 'D:\work\Redis-8.10.2-Windows-x64-msys2'
$ApiLocalCfg = 'D:\work\runtime-logs\api-local.properties'
$LegacyApiStarter = 'D:\work\runtime-logs\start-api-v3.ps1'
$Maven       = 'D:\work\apache-maven\bin\mvn.cmd'
$PidFile     = Join-Path $LogDir 'v3-pids.json'

$Ports = [ordered]@{
    OpenGauss = 5432
    MySQL8    = 3307
    Redis     = 6379
    Kafka     = 9092
    ES        = 9200
    Api       = 9902
    Backend   = 9989
}

if ($MemoryProfile -eq 'Low') {
    $JavaHeapArgs = @('-Xms256m', '-Xmx768m')
    $BudgetGB = 2.6
} else {
    $JavaHeapArgs = @('-Xms512m', '-Xmx1g')
    $BudgetGB = 3.3
}

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null }
$script:StartedPids = @()

# ---------------------------------------------------------------- 工具函数
function Write-Step {
    param([string]$Name, [string]$State, [string]$Detail = '')
    $color = switch ($State) {
        'OK'    { 'Green' }
        'SKIP'  { 'Cyan' }
        'WARN'  { 'Yellow' }
        'FAIL'  { 'Red' }
        default { 'Gray' }
    }
    $msg = '[{0,-4}] {1,-12} {2}' -f $State, $Name, $Detail
    Write-Host $msg -ForegroundColor $color
}

function Test-TcpPort {
    param([int]$Port, [string]$HostName = '127.0.0.1', [int]$TimeoutMs = 400)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $iar = $client.BeginConnect($HostName, $Port, $null, $null)
        if (-not $iar.AsyncWaitHandle.WaitOne($TimeoutMs, $false)) { return $false }
        $client.EndConnect($iar)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Wait-TcpPort {
    param([string]$Name, [int]$Port, [string]$HostName = '127.0.0.1', [int]$Seconds = 90)
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-TcpPort -Port $Port -HostName $HostName) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Get-JavaByJar {
    param([string]$JarPattern)
    @(Get-CimInstance Win32_Process -Filter "name='java.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -like "*$JarPattern*" })
}

function Get-PortOwner {
    param([int]$Port)
    $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $c) { return $null }
    return (Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue)
}

function Remove-OldLog {
    param([string]$Prefix)
    foreach ($kind in @('out', 'err')) {
        $p = Join-Path $LogDir "$Prefix.$kind.log"
        if ([System.IO.File]::Exists($p)) { [System.IO.File]::Delete($p) }
    }
}

function Start-Detached {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory = $LogDir,
        [hashtable]$ExtraEnv = @{},
        [string]$LogPrefix
    )
    Remove-OldLog -Prefix $LogPrefix
    $out = Join-Path $LogDir "$LogPrefix.out.log"
    $err = Join-Path $LogDir "$LogPrefix.err.log"
    # 子进程在创建时快照环境变量，启动后立即恢复，避免污染后续服务
    $saved = @{}
    foreach ($k in $ExtraEnv.Keys) {
        $saved[$k] = (Get-Item -Path "Env:$k" -ErrorAction SilentlyContinue).Value
        Set-Item -Path "Env:$k" -Value ([string]$ExtraEnv[$k])
    }
    try {
        $p = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList `
            -WorkingDirectory $WorkingDirectory -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput $out -RedirectStandardError $err
    } finally {
        foreach ($k in $saved.Keys) {
            if ($null -eq $saved[$k]) { Remove-Item -Path "Env:$k" -ErrorAction SilentlyContinue }
            else { Set-Item -Path "Env:$k" -Value ([string]$saved[$k]) }
        }
    }
    $script:StartedPids += [pscustomobject]@{
        Name = $Name; Pid = $p.Id; StartedAt = (Get-Date).ToString('s')
    }
    return $p
}

function New-RandomHex {
    param([int]$Bytes = 24)
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $buf = New-Object byte[] $Bytes
        $rng.GetBytes($buf)
        return (-join ($buf | ForEach-Object { $_.ToString('x2') }))
    } finally { $rng.Dispose() }
}

function Get-LegacyEnvValue {
    param([string]$Name)
    if (-not (Test-Path $LegacyApiStarter)) { return $null }
    $pattern = '^\s*\$env:' + [regex]::Escape($Name) + "\s*=\s*'([^']*)'"
    foreach ($line in [System.IO.File]::ReadAllLines($LegacyApiStarter)) {
        $m = [regex]::Match($line, $pattern)
        if ($m.Success) { return $m.Groups[1].Value }
    }
    return $null
}

function Show-Status {
    Write-Host ''
    Write-Host '=== V3 联调环境状态 ===' -ForegroundColor White
    Write-Host ('{0,-12} {1,-7} {2,-8} {3}' -f 'SERVICE', 'PORT', 'STATE', 'OWNER')
    foreach ($entry in $Ports.GetEnumerator()) {
        $name = $entry.Key; $port = $entry.Value
        $up = Test-TcpPort -Port $port
        $owner = ''
        if ($up) {
            $pr = Get-PortOwner -Port $port
            if ($pr) { $owner = "$($pr.ProcessName) (pid=$($pr.Id))" }
        }
        $state = if ($up) { 'UP' } else { 'DOWN' }
        $color = if ($up) { 'Green' } else { 'Gray' }
        Write-Host ('{0,-12} {1,-7} {2,-8} {3}' -f $name, $port, $state, $owner) -ForegroundColor $color
    }
    $be = Get-JavaByJar -JarPattern 'ruoyi-admin.jar'
    $ap = Get-JavaByJar -JarPattern 'pro-business-api-1.0.jar'
    Write-Host ''
    Write-Host "backend java instances = $($be.Count) ; api java instances = $($ap.Count)" -ForegroundColor White
    $os = Get-CimInstance Win32_OperatingSystem
    Write-Host ("host free RAM = {0:N2} GB" -f ($os.FreePhysicalMemory / 1MB)) -ForegroundColor White
}

function Stop-Started {
    if (-not (Test-Path $PidFile)) {
        Write-Step 'Stop' 'WARN' '无 v3-pids.json，未停止任何进程（避免误杀）'
        return
    }
    $list = @(Get-Content -Path $PidFile -Raw -Encoding UTF8 | ConvertFrom-Json)
    foreach ($item in $list) {
        $pr = Get-Process -Id $item.Pid -ErrorAction SilentlyContinue
        if ($pr) {
            Stop-Process -Id $item.Pid -Force -ErrorAction SilentlyContinue
            Write-Step 'Stop' 'OK' "$($item.Name) pid=$($item.Pid)"
        } else {
            Write-Step 'Stop' 'SKIP' "$($item.Name) pid=$($item.Pid) 已退出"
        }
    }
    [System.IO.File]::Delete($PidFile)
}

# ---------------------------------------------------------------- 状态 / 停止
if ($Status) { Show-Status; return }
if ($Stop)   { Stop-Started; return }

# ---------------------------------------------------------------- 前置检查
Write-Host ''
Write-Host '=== car-monit V3 一键启动 ===' -ForegroundColor White
$os = Get-CimInstance Win32_OperatingSystem
$freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
Write-Host ("内存档位 = {0}；宿主可用 = {1} GB；本档预算 ≈ {2} GB" -f $MemoryProfile, $freeGB, $BudgetGB) -ForegroundColor White
if ($freeGB -lt $BudgetGB) {
    Write-Step 'Memory' 'WARN' "宿主可用内存低于预算，建议加 -Minimal 或先释放内存（当前页交换可能变重）"
}

foreach ($f in @($Java8, $BackendJar, $ApiJar, $Maven)) {
    if (-not (Test-Path $f)) { Write-Step 'Precheck' 'FAIL' "缺少文件: $f"; return }
}
if (-not (Test-Path $ApiLocalCfg)) {
    Write-Step 'Precheck' 'WARN' "缺少 $ApiLocalCfg，api 将使用 application.yml 默认数据源口令"
} elseif ((Get-Item $ApiLocalCfg).Length -eq 0) {
    Write-Step 'Precheck' 'WARN' "$ApiLocalCfg 为空文件；请配置 SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD，否则 api 可能连不上 openGauss"
}

# 环境变量（不落盘、不打印值）
if (Test-Path $EnvFile) { . $EnvFile }

$tokApi = $env:TRAFFIC_INTERNAL_TOKEN
$tokBe  = $env:TRAFFIC_API_INTERNAL_TOKEN
if ($tokApi -and $tokBe -and $tokApi -ne $tokBe) {
    Write-Step 'Token' 'FAIL' '两侧内部端点令牌不一致，会导致 backend 调 api 全部 403'
    return
}
if (-not $tokApi) { $tokApi = New-RandomHex -Bytes 24 }
$env:TRAFFIC_INTERNAL_TOKEN = $tokApi
$env:TRAFFIC_API_INTERNAL_TOKEN = $tokApi
if (-not $env:EXPORT_DOWNLOAD_SECRET) { $env:EXPORT_DOWNLOAD_SECRET = New-RandomHex -Bytes 32 }
Write-Step 'Token' 'OK' '内部令牌与导出下载签名密钥已就绪（会话级随机值，不落盘）'

if (-not $env:CARMONIT_MYSQL_USERNAME) {
    $v = Get-LegacyEnvValue -Name 'CARMONIT_MYSQL_USERNAME'
    if ($v) { $env:CARMONIT_MYSQL_USERNAME = $v }
}
if (-not $env:CARMONIT_MYSQL_PASSWORD) {
    $v = Get-LegacyEnvValue -Name 'CARMONIT_MYSQL_PASSWORD'
    if ($v) { $env:CARMONIT_MYSQL_PASSWORD = $v }
}
if (-not $env:CARMONIT_MYSQL_USERNAME) {
    Write-Step 'MySQL' 'WARN' '未配置 CARMONIT_MYSQL_USERNAME/PASSWORD，api 车牌颜色字典读取可能失败'
}

# ---------------------------------------------------------------- 可选构建
if ($Build) {
    $env:JAVA_HOME = 'D:\jdk\jdk1.8.0_202'
    foreach ($p in @((Join-Path $ApiRoot 'pom.xml'), (Join-Path $BackendRoot 'pom.xml'))) {
        Write-Step 'Build' 'OK' "mvn package $p"
        & $Maven -f $p -o -B -q -DskipTests package
        if ($LASTEXITCODE -ne 0) { Write-Step 'Build' 'FAIL' "$p 构建失败"; return }
    }
}

# ---------------------------------------------------------------- 1. openGauss（只检查，不新建实例）
if (-not $SkipOpenGauss) {
    if (Test-TcpPort -HostName '192.168.56.10' -Port 5432) {
        Write-Step 'OpenGauss' 'SKIP' '192.168.56.10:5432 已可达'
    } elseif (Test-TcpPort -Port 5432) {
        Write-Step 'OpenGauss' 'SKIP' '127.0.0.1:5432 已可达（WSL/端口转发）'
    } elseif ($env:V3_VM_PASSWORD) {
        $py = "import paramiko,os;c=paramiko.SSHClient();c.set_missing_host_key_policy(paramiko.AutoAddPolicy());c.connect('192.168.56.10',22,'root',os.environ['V3_VM_PASSWORD'],timeout=10);i,o,e=c.exec_command('docker start opengauss');print(o.read().decode().strip());c.close()"
        try {
            & python -c $py 2>&1 | Out-Null
            Write-Step 'OpenGauss' 'OK' '已尝试在虚拟机启动 opengauss 容器'
        } catch {
            Write-Step 'OpenGauss' 'WARN' "SSH 启动失败: $($_.Exception.Message)"
        }
    } else {
        Write-Step 'OpenGauss' 'WARN' '5432 不可达且未设置 V3_VM_PASSWORD；请在虚拟机执行 docker start opengauss'
    }
}

# ---------------------------------------------------------------- 2. MySQL8（只检查 3307）
if (Test-TcpPort -Port 3307) {
    Write-Step 'MySQL8' 'SKIP' '3307 已可达（遵守「不在其它 data 目录另起实例」）'
} else {
    Write-Step 'MySQL8' 'WARN' '3307 不可达；请确认现有 mysql8 实例/WSL 转发，本脚本不会另起 mysqld'
}

# ---------------------------------------------------------------- 3. Redis
if (Test-TcpPort -Port 6379) {
    Write-Step 'Redis' 'SKIP' '6379 已监听'
} else {
    $exe = Join-Path $RedisHome 'redis-server.exe'
    $conf = Join-Path $RedisHome 'redis.conf'
    if (-not (Test-Path $exe)) { Write-Step 'Redis' 'FAIL' "缺少 $exe" }
    else {
        Start-Detached -Name 'Redis' -FilePath $exe -ArgumentList @($conf) -WorkingDirectory $RedisHome -LogPrefix 'v3-redis' | Out-Null
        if (Wait-TcpPort -Name 'Redis' -Port 6379 -Seconds 30) { Write-Step 'Redis' 'OK' '6379 就绪' }
        else { Write-Step 'Redis' 'FAIL' "启动超时，检查 $LogDir\v3-redis.err.log" }
    }
}

# ---------------------------------------------------------------- 4. Kafka (KRaft 单节点)
if (Test-TcpPort -Port 9092) {
    Write-Step 'Kafka' 'SKIP' '9092 已监听'
} elseif ($Minimal) {
    Write-Step 'Kafka' 'SKIP' '-Minimal：不主动启动 Kafka'
} else {
    $bat = Join-Path $KafkaHome 'bin\windows\kafka-server-start.bat'
    $conf = Join-Path $KafkaHome 'config\server.properties'
    $dataDir = 'D:\work\kafka-data-20261108'
    if (-not (Test-Path $bat) -or -not (Test-Path $conf)) {
        Write-Step 'Kafka' 'FAIL' '缺少启动脚本或 server.properties'
    } elseif (-not (Test-Path (Join-Path $dataDir 'meta.properties'))) {
        Write-Step 'Kafka' 'WARN' "KRaft 存储未格式化: $dataDir；请先执行 kafka-storage.bat format"
    } else {
        Start-Detached -Name 'Kafka' -FilePath 'cmd.exe' `
            -ArgumentList @('/c', ('"{0}" "{1}"' -f $bat, $conf)) -WorkingDirectory $KafkaHome `
            -LogPrefix 'v3-kafka' -ExtraEnv @{
                JAVA_HOME = $Java21Home
                KAFKA_HEAP_OPTS = '-Xms256M -Xmx512M'
            } | Out-Null
        if (Wait-TcpPort -Name 'Kafka' -Port 9092 -Seconds ([Math]::Min($TimeoutSec, 90))) { Write-Step 'Kafka' 'OK' '9092 就绪（JDK21 / 512m 堆）' }
        else { Write-Step 'Kafka' 'FAIL' "启动超时，检查 $LogDir\v3-kafka.err.log" }
    }
}

# ---------------------------------------------------------------- 5. Elasticsearch
if (Test-TcpPort -Port 9200) {
    Write-Step 'ES' 'SKIP' '9200 已监听'
} elseif ($Minimal) {
    Write-Step 'ES' 'SKIP' '-Minimal：不主动启动 ES'
} else {
    $bat = Join-Path $EsHome 'bin\elasticsearch.bat'
    $optsDir = Join-Path $EsHome 'config\jvm.options.d'
    $heapFile = Join-Path $optsDir 'v3-heap.options'
    if (-not (Test-Path $bat)) { Write-Step 'ES' 'FAIL' "缺少 $bat" }
    else {
        if (-not (Test-Path $heapFile)) {
            New-Item -ItemType Directory -Force -Path $optsDir | Out-Null
            [System.IO.File]::WriteAllText($heapFile, "-Xms512m`n-Xmx512m`n")
            Write-Step 'ES' 'OK' '已写入 config\jvm.options.d\v3-heap.options 限制 512m 堆'
        }
        Start-Detached -Name 'ES' -FilePath 'cmd.exe' `
            -ArgumentList @('/c', ('"{0}"' -f $bat)) -WorkingDirectory $EsHome `
            -LogPrefix 'v3-es' | Out-Null
        if (Wait-TcpPort -Name 'ES' -Port 9200 -Seconds $TimeoutSec) { Write-Step 'ES' 'OK' '9200 就绪（512m 堆）' }
        else { Write-Step 'ES' 'FAIL' "启动超时，检查 $LogDir\v3-es.err.log" }
    }
}

# ---------------------------------------------------------------- 6. api (9902)
if (-not $SkipApi) {
    $existing = Get-JavaByJar -JarPattern 'pro-business-api-1.0.jar'
    if (Test-TcpPort -Port 9902) {
        Write-Step 'Api' 'SKIP' '9902 已监听'
    } elseif ($existing.Count -gt 0) {
        Write-Step 'Api' 'SKIP' "检测到 $($existing.Count) 个 api java 进程，避免重复启动"
    } else {
        $javaArgs = @() + $JavaHeapArgs + @(
            '-Dserver.port=9902', '-jar', $ApiJar,
            '--spring.config.additional-location=file:D:/work/runtime-logs/api-local.properties'
        )
        $env:TRAFFIC_QUERY_ENGINE = 'es'
        $env:TRAFFIC_BIGSCREEN_STATS_ENABLED = 'true'
        $env:TRAFFIC_BIGSCREEN_ETL_ENABLED = 'true'
        $env:TRAFFIC_SYNC_ENABLED = 'true'
        $env:TRAFFIC_SYNC_CAR_WARNING_ENABLED = 'true'
        $env:TRAFFIC_RECONCILE_ENABLED = 'true'
        Start-Detached -Name 'Api' -FilePath $Java8 -ArgumentList $javaArgs `
            -WorkingDirectory (Join-Path $ApiRoot 'pro-business-api') -LogPrefix 'v3-api' | Out-Null
        if (Wait-TcpPort -Name 'Api' -Port 9902 -Seconds $TimeoutSec) { Write-Step 'Api' 'OK' '9902 就绪' }
        else { Write-Step 'Api' 'FAIL' "启动超时，检查 $LogDir\v3-api.err.log" }
    }
}

# ---------------------------------------------------------------- 7. backend (9989)
if (-not $SkipBackend) {
    $existing = Get-JavaByJar -JarPattern 'ruoyi-admin.jar'
    if (Test-TcpPort -Port 9989) {
        Write-Step 'Backend' 'SKIP' '9989 已监听'
    } elseif ($existing.Count -gt 0) {
        Write-Step 'Backend' 'SKIP' "检测到 $($existing.Count) 个 backend java 进程，避免重复启动"
    } elseif (-not (Test-TcpPort -Port 9902)) {
        Write-Step 'Backend' 'WARN' 'api 9902 未就绪，backend 仍会启动但统计链路会降级'
    }
    if (-not (Test-TcpPort -Port 9989)) {
        if ((Get-JavaByJar -JarPattern 'ruoyi-admin.jar').Count -eq 0) {
            $javaArgs = @() + $JavaHeapArgs + @('-Dserver.port=9989', '-jar', $BackendJar)
            $env:VEHICLE_MONITOR_BASE_URL = 'http://127.0.0.1:9902'
            Start-Detached -Name 'Backend' -FilePath $Java8 -ArgumentList $javaArgs `
                -WorkingDirectory (Join-Path $BackendRoot 'ruoyi-admin') -LogPrefix 'v3-backend' | Out-Null
            if (Wait-TcpPort -Name 'Backend' -Port 9989 -Seconds $TimeoutSec) { Write-Step 'Backend' 'OK' '9989 就绪' }
            else { Write-Step 'Backend' 'FAIL' "启动超时，检查 $LogDir\v3-backend.err.log" }
        }
    }
}

# ---------------------------------------------------------------- 保存 PID / 汇总
try {
    if ($script:StartedPids.Count -gt 0) {
        $json = $script:StartedPids | ConvertTo-Json -Depth 3
        [System.IO.File]::WriteAllText($PidFile, $json)
    }
} catch {
    Write-Step 'PidFile' 'WARN' "写入失败: $($_.Exception.Message)"
}

Write-Host ''
Show-Status
Write-Host ''
Write-Host '关键地址:' -ForegroundColor White
Write-Host '  backend  http://127.0.0.1:9989'
Write-Host '  api      http://127.0.0.1:9902  (需 X-Internal-Token 头)'
Write-Host '  ES       http://127.0.0.1:9200'
Write-Host ("日志      {0}\v3-*.{{out,err}}.log" -f $LogDir)
Write-Host '停止      .\scripts\v3\start-v3-all.ps1 -Stop' -ForegroundColor White
