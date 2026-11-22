# @description 历史脚本 start-api-v3.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage powershell -File start-api-v3.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
$ErrorActionPreference = 'Continue'
# 本机联调部署：显式启用 ES；启动就绪检测失败会自动回退 legacy
$env:TRAFFIC_QUERY_ENGINE = 'es'
$env:TRAFFIC_BIGSCREEN_STATS_ENABLED = 'true'
$env:TRAFFIC_BIGSCREEN_ETL_ENABLED = 'true'
$env:TRAFFIC_SYNC_ENABLED = 'true'
$env:TRAFFIC_SYNC_CAR_WARNING_ENABLED = 'true'
$env:TRAFFIC_RECONCILE_ENABLED = 'true'
$env:CARMONIT_MYSQL_USERNAME = 'carmonit_ro'
$env:CARMONIT_MYSQL_PASSWORD = 'CarMonitRo@2026'
Set-Location 'D:\work\IdeaProjects\car-monit-api-java-V3\pro-business-api'
& 'D:\jdk\jdk1.8.0_202\bin\java.exe' -Xms512m -Xmx1g '-Dserver.port=9902' -jar 'D:\work\IdeaProjects\car-monit-api-java-V3\pro-business-api\target\pro-business-api-1.0.jar' '--spring.config.additional-location=file:D:/work/runtime-logs/api-local.properties' *> 'D:\work\runtime-logs\api-v3.console.log'
