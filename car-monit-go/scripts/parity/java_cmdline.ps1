$exe = Get-CimInstance Win32_Process -Filter "Name='java.exe'"
foreach ($e in $exe) {
  $c = $e.CommandLine
  if ($null -ne $c -and $c.Length -gt 300) { $c = $c.Substring(0, 300) }
  Write-Output ("JAVA PID=" + $e.ProcessId + " PARENT=" + $e.ParentProcessId + " CMD=" + $c)
}
