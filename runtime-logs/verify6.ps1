# @description 历史脚本 verify6.ps1：验证配置、构建或安全不变量；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage powershell -File verify6.ps1 [params]；参数含义见脚本原有注释。
# @dependencies Maven 与对应 JDK
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

