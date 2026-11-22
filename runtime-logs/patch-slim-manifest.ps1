# @description 历史脚本 patch-slim-manifest.ps1：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage powershell -File patch-slim-manifest.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
$p = 'D:\work\runtime-logs\manifests-final.yaml'
$t = [System.IO.File]::ReadAllText($p) -replace "`r`n", "`n"
$t = $t.Replace('image: car-monit-api:local', 'image: car-monit-api:slim')
$t = $t.Replace('image: car-monit-backend:local', 'image: car-monit-backend:slim')
$t = $t.Replace('memory: 300Mi', 'memory: 400Mi')
$t = $t.Replace('- -Xms20m', '- -Xms32m')
$t = $t.Replace('- -Xmx64m', '- -Xmx96m')
$t = $t.Replace('- -XX:MaxMetaspaceSize=136m', '- -XX:MaxMetaspaceSize=144m')
$t = $t.Replace('- -XX:ReservedCodeCacheSize=12m', '- -XX:ReservedCodeCacheSize=32m')
$t = $t.Replace('- -XX:MaxDirectMemorySize=2m', '- -XX:MaxDirectMemorySize=16m')
$t = $t.Replace('- -Xss192k', '- -Xss512k')
$t = $t.Replace('            - -Dio.netty.allocator.type=unpooled' + "`n", '')
$t = $t.Replace('- --server.tomcat.max-connections=32', '- --server.tomcat.max-connections=200')
$t = $t.Replace('- --server.tomcat.threads.max=2', '- --server.tomcat.threads.max=8')
[System.IO.File]::WriteAllText($p, $t, (New-Object System.Text.UTF8Encoding($false)))
'patched slim manifest'
