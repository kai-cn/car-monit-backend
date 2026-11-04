param(
  [string]$Repo = "D:\work\IdeaProjects\car-monit-backend-new\car-monit-go",
  [string]$Exe = "bin\carmonit-server.exe",
  [string]$Cfg = "$env:TEMP\config.ref9902.yaml",
  [string]$Log = "$env:TEMP\go-ref-9986.log"
)
$p = Start-Process -FilePath (Join-Path $Repo $Exe) `
     -ArgumentList @("-c", $Cfg) `
     -WorkingDirectory $Repo `
     -RedirectStandardOutput $Log -RedirectStandardError ($Log + ".err") `
     -PassThru -WindowStyle Hidden
Write-Output ("STARTED PID=" + $p.Id + " cfg=" + $Cfg)
