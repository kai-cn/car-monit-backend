$log = 'D:\work\runtime-logs\win-mem-samples.log'
Remove-Item $log -ErrorAction SilentlyContinue
1..200 | ForEach-Object {
    $vm = (Get-Process vmmemWSL -ErrorAction SilentlyContinue).WorkingSet64 / 1MB
    $free = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB
    "$(Get-Date -Format HH:mm:ss) vmmem_mb=$([math]::Round($vm,0)) free_gb=$([math]::Round($free/1024,2))" |
        Out-File -Append -FilePath $log -Encoding UTF8
    Start-Sleep -Seconds 3
}
