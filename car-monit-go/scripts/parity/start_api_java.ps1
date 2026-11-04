param(
  [string]$ProjDir = "D:\work\IdeaProjects\car-monit-api\pro-business-api",
  [int]$Port = 9902,
  [string]$Jar = "target/pro-business-api-1.0.jar",
  [string]$Log = "$env:TEMP\api-java-9902.log"
)
$java = "D:\jdk\jdk1.8.0_202\bin\java.exe"
$argLine = "-Xmx2048m -Dserver.port=$Port -jar $Jar"
$p = Start-Process -FilePath $java -ArgumentList $argLine -WorkingDirectory $ProjDir `
     -RedirectStandardOutput $Log -RedirectStandardError ($Log + ".err") -PassThru -WindowStyle Hidden
Write-Output ("STARTED PID=" + $p.Id + " port=" + $Port)
