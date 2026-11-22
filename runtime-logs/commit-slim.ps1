# @description 历史脚本 commit-slim.ps1：创建集中提交或改写指定提交；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage powershell -File commit-slim.ps1 [params]；参数含义见脚本原有注释。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

$beDoc = 'd:\work\IdeaProjects\car-monit-backend-jdk17\docs\v3\jar-slim-and-db-limits-verification.md'

$src = [System.IO.File]::ReadAllText($beDoc)

$headerLine = '# jar 瘦身 / 镜像减重 / ERROR 日志 / DB 内存上限实测记录'

$apiDoc = $src.Replace($headerLine, $headerLine + "`n`n> Mirror of the backend verification doc.")

$branches = @(

 'car-monit-backend-jdk17','car-monit-backend-jdk21','car-monit-backend-jdk25',

 'car-monit-api-jdk17','car-monit-api-jdk21','car-monit-api-jdk25'

)

$msg = @'

perf(slim): slim fat jar / jlink image / ERROR-only logging / measured DB limits



- api: exclude 21 provided Flink jars and foreign-platform Netty natives from repackage (jar -23.3%)

- backend: exclude 0-reference calcite/groovy/aliyun-mns (jar -10.7%)

- image: 66MB jlink runtime + flattened 255MB system layer; api 1.04GB->537MB, backend 965MB->504MB

- fonts: real libfontconfig/libfreetype + DejaVuSans from oracle_11g; captcha restored in cluster

- logging: root/loggers/MyBatis/p6spy/Forest all ERROR, NopStatusListener added

- DB: measured peaks mysql 32.02MiB / opengauss 81.02MiB; 500m hard cap then tightened to 256m with regression

- cluster: 400Mi x 3+3 replicas, full captcha login / auth APIs / cross-service export all 200, workingSet 283-338MiB

- all 6 branches mvn -DskipTests=false test passed

'@

foreach ($b in $branches) {

  $root = "d:\work\IdeaProjects\$b"

  $docDir = Join-Path $root 'docs\v3'

  New-Item -ItemType Directory -Force -Path $docDir | Out-Null

  $doc = Join-Path $docDir 'jar-slim-and-db-limits-verification.md'

  if ($b.StartsWith('car-monit-api')) { [System.IO.File]::WriteAllText($doc, $apiDoc, (New-Object System.Text.UTF8Encoding($false))) }

  else { [System.IO.File]::WriteAllText($doc, $src, (New-Object System.Text.UTF8Encoding($false))) }

  Set-Location $root

  & git add -A 2>&1 | Out-Null

  & git add -f (Join-Path 'docs\v3' 'jar-slim-and-db-limits-verification.md') 2>&1 | Out-Null

  & git -c core.quotepath=false commit -q -m $msg 2>&1 | Out-Null

  $sha = & git --no-pager log --oneline -1

  '{0} -> {1}' -f $b, $sha

}

