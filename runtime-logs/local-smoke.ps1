# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
$ErrorActionPreference = 'Continue'
$jdkList = @(
    @{ name = 'jdk17'; home = 'D:\jdk\temurin-17\jdk-17.0.21+9'; dir = 'car-monit-api-jdk17'; spec = 17 },
    @{ name = 'jdk21'; home = 'D:\jdk\temurin-21.0.12.1_1\jdk-21.0.12.1+1'; dir = 'car-monit-api-jdk21'; spec = 21 },
    @{ name = 'jdk25'; home = 'D:\jdk\temurin-25.0.4.1_1\jdk-25.0.4.1+1'; dir = 'car-monit-api-jdk25'; spec = 25 }
)
$java = @'
import java.lang.reflect.Method;
public class AddOpensSmoke {
  public static void main(String[] args) throws Exception {
    Method m = Object.class.getDeclaredMethod("clone");
    m.setAccessible(true);
    System.out.println("add-opens effective");
  }
}
'@
$work = 'D:\work\runtime-logs\smoke'
New-Item -ItemType Directory -Force -Path $work | Out-Null
[System.IO.File]::WriteAllText("$work\AddOpensSmoke.java", $java, (New-Object System.Text.UTF8Encoding($false)))

foreach ($j in $jdkList) {
    $javac = "$($j.home)\bin\javac.exe"
    $javaExe = "$($j.home)\bin\java.exe"
    & $javac -encoding UTF-8 -d $work "$work\AddOpensSmoke.java" 2>&1 | Out-Null
    $without = & $javaExe -cp $work AddOpensSmoke 2>&1
    $with = & $javaExe '--add-opens=java.base/java.lang=ALL-UNNAMED' -cp $work AddOpensSmoke 2>&1
    $cls = Get-ChildItem -Path "d:\work\IdeaProjects\$($j.dir)\pro-business-api\target\classes" -Recurse -Filter '*.class' | Select-Object -First 1
    $verbose = & "$($j.home)\bin\javap.exe" -verbose $cls.FullName 2>&1
    $majorLine = ($verbose | Select-String -Pattern 'major version').Line.Trim()
    $major = ($majorLine -split '\s+')[-1]
    "{0}: without_flag_fails={1} with_flag_ok={2} major={3} expected={4}" -f `
        $j.name, ($LASTEXITCODE -ne 0 -or ($without -match 'InaccessibleObjectException')), `
        ($with -match 'add-opens effective'), $major, (44 + $j.spec)
}
