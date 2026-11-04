param(
  [string]$JarDir = "D:\work\IdeaProjects\car-monit-backend-new\ruoyi-admin\target",
  [int]$Port = 9987,
  [string]$ApiUrl = "http://127.0.0.1:9902",
  [string]$Log = "C:\Users\abelz\AppData\Local\Temp\java-ref-9987.log"
)
$java = "D:\jdk\jdk1.8.0_202\bin\java.exe"
$argLine = "-Xmx1g -jar ruoyi-admin.jar --server.port=$Port --vehicleMonitor.baseUrl=$ApiUrl"
$p = Start-Process -FilePath $java -ArgumentList $argLine -WorkingDirectory $JarDir `
     -RedirectStandardOutput $Log -RedirectStandardError ($Log + ".err") -PassThru -WindowStyle Hidden
Write-Output ("STARTED PID=" + $p.Id + " port=" + $Port + " api=" + $ApiUrl)
