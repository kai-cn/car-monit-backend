# Kafka 和 Elasticsearch 下载脚本
# 使用方法：在 PowerShell 中执行 .\download-packages.ps1
# 目标目录：D:\work\

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Kafka & Elasticsearch 下载工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查目标目录
$targetDir = "D:\work"
if (-not (Test-Path $targetDir)) {
    Write-Host "创建目录: $targetDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

# 下载目录
$downloadDir = "$targetDir\downloads"
if (-not (Test-Path $downloadDir)) {
    New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
}

Write-Host "下载目录: $downloadDir" -ForegroundColor Green
Write-Host ""

# 软件下载配置
$packages = @(
    @{
        Name = "JDK 8 (可选，如未安装)"
        Url = "https://download.oracle.com/java/8/latest/jdk-8_windows-x64_bin.zip"
        FileName = "jdk-8-windows-x64.zip"
        Note = "需要 Oracle 账号登录下载，建议手动下载"
    },
    @{
        Name = "ZooKeeper 3.7.1"
        Url = "https://archive.apache.org/dist/zookeeper/zookeeper-3.7.1/apache-zookeeper-3.7.1-bin.tar.gz"
        FileName = "apache-zookeeper-3.7.1-bin.tar.gz"
    },
    @{
        Name = "Kafka 2.8.2 (Scala 2.13)"
        Url = "https://archive.apache.org/dist/kafka/2.8.2/kafka_2.13-2.8.2.tgz"
        FileName = "kafka_2.13-2.8.2.tgz"
    },
    @{
        Name = "Elasticsearch 7.15.2"
        Url = "https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.15.2-windows-x86_64.zip"
        FileName = "elasticsearch-7.15.2-windows-x86_64.zip"
    },
    @{
        Name = "Kibana 7.15.2 (可选)"
        Url = "https://artifacts.elastic.co/downloads/kibana/kibana-7.15.2-windows-x86_64.zip"
        FileName = "kibana-7.15.2-windows-x86_64.zip"
    }
)

# 下载函数
function Download-File {
    param(
        [string]$Url,
        [string]$OutputPath,
        [string]$Name
    )
    
    if (Test-Path $OutputPath) {
        Write-Host "✓ $Name 已存在，跳过下载" -ForegroundColor Green
        return $true
    }
    
    Write-Host "正在下载: $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($Url, $OutputPath)
        Write-Host "✓ $Name 下载完成" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ $Name 下载失败: $_" -ForegroundColor Red
        Write-Host "  请手动从以下地址下载: $Url" -ForegroundColor Yellow
        return $false
    }
}

# 执行下载
Write-Host "开始下载软件包..." -ForegroundColor Cyan
Write-Host ""

$downloadCount = 0
foreach ($pkg in $packages) {
    $outputPath = Join-Path $downloadDir $pkg.FileName
    if (Download-File -Url $pkg.Url -OutputPath $outputPath -Name $pkg.Name) {
        $downloadCount++
    }
    if ($pkg.Note) {
        Write-Host "  注意: $($pkg.Note)" -ForegroundColor Magenta
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  下载完成! $downloadCount/$($packages.Count) 个包" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下载位置: $downloadDir" -ForegroundColor Green
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "1. 解压所有下载的压缩包到 D:\work\"
Write-Host "2. 参考 KAFKA_ES_INSTALL_GUIDE.md 进行配置和启动"
Write-Host ""
