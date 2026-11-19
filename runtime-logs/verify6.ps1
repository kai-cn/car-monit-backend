# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only verification of a security or build invariant.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
$pairs = @(
 @('car-monit-api-jdk17','D:\jdk\temurin-17\jdk-17.0.21+9'),
 @('car-monit-api-jdk21','D:\jdk\temurin-21.0.12.1_1\jdk-21.0.12.1+1'),
 @('car-monit-api-jdk25','D:\jdk\temurin-25.0.4.1_1\jdk-25.0.4.1+1'),
 @('car-monit-backend-jdk17','D:\jdk\temurin-17\jdk-17.0.21+9'),
 @('car-monit-backend-jdk21','D:\jdk\temurin-21.0.12.1_1\jdk-21.0.12.1+1'),
 @('car-monit-backend-jdk25','D:\jdk\temurin-25.0.4.1_1\jdk-25.0.4.1+1')
)
foreach ($p in $pairs) {
  Set-Location "d:\work\IdeaProjects\$($p[0])"
  $env:JAVA_HOME = $p[1]
  $env:MAVEN_OPTS = '-Duser.language=en'
  $out = & 'D:\work\apache-maven\bin\mvn.cmd' -B -DskipTests=false -q test 2>&1
  $bad = $out | Select-String -Pattern 'BUILD FAILURE|\[ERROR\]' | Select-Object -First 2
  $status = 'OK'
  if ($bad) { $status = ($bad | ForEach-Object { $_.Line.Trim() }) -join ' | ' }
  "{0}: {1}" -f $p[0], $status
}
