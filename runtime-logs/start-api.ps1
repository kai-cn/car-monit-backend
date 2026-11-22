# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
$ErrorActionPreference = 'Continue'
Set-Location 'D:\work\IdeaProjects\car-monit-api\pro-business-api'
& 'D:\jdk\jdk1.8.0_202\bin\java.exe' -Xms512m -Xmx1g '-Dserver.port=9902' -jar 'D:\work\IdeaProjects\car-monit-api\pro-business-api\target\pro-business-api-1.0.jar' '--spring.config.additional-location=file:D:/work/runtime-logs/api-local.properties' *> 'D:\work\runtime-logs\api.console.log'
