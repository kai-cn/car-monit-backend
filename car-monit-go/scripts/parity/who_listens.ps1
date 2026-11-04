$ports = @(9901,9902,9903,9911,9922,9988,9989,9990,9991,9992,9993)
foreach ($p in $ports) {
  $c = Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $c) {
    Write-Output ($p.ToString() + " NOT-LISTENING")
    continue
  }
  $pid2 = $c.OwningProcess
  $pr = Get-CimInstance Win32_Process -Filter "ProcessId=$pid2"
  $cmd = $pr.CommandLine
  if ($null -ne $cmd -and $cmd.Length -gt 170) { $cmd = $cmd.Substring(0,170) }
  Write-Output ($p.ToString() + " PID=" + $pid2 + " start=" + $pr.CreationDate + " :: " + $cmd)
}
