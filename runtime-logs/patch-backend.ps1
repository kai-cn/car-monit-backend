# @description 历史脚本 patch-backend.ps1：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage powershell -File patch-backend.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

$p = 'D:\work\runtime-logs\manifests.yaml'

$t = [System.IO.File]::ReadAllText($p) -replace "`r`n", "`n"



$old = @'

            - -Xms20m

            - -Xmx56m

            - -XX:MaxMetaspaceSize=120m

            - -XX:CompressedClassSpaceSize=12m

'@ -replace "`r?`n", "`n"

$new = @'

            - -Xms20m

            - -Xmx64m

            - -XX:MaxMetaspaceSize=112m

            - -XX:CompressedClassSpaceSize=12m

'@ -replace "`r?`n", "`n"



# only the backend block carries --server.port=9989; replace its first occurrence after that marker

$marker = '            - --server.port=9989'

$idx = $t.IndexOf($marker)

if ($idx -lt 0) { throw 'backend marker missing' }

$before = $t.Substring(0, $idx)

$after = $t.Substring($idx)

# backend jvm block is right before the marker; patch the last Xmx/MaxMetaspace in $before

$bIdx = $before.LastIndexOf('- -Xms20m')

if ($bIdx -lt 0) { throw 'backend jvm block missing' }

$bBefore = $before.Substring(0, $bIdx)

$bBlock = $before.Substring($bIdx)

$bBlock = $bBlock.Replace('- -Xmx56m', '- -Xmx64m').Replace('- -XX:MaxMetaspaceSize=120m', '- -XX:MaxMetaspaceSize=112m')

$t = $bBefore + $bBlock + $after



$t = $t.Replace(

    '            - --spring.datasource.druid.master.url=jdbc:p6spy:mysql://172.18.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8&allowMultiQueries=true',

    @'

            - --spring.datasource.driverClassName=com.mysql.cj.jdbc.Driver

            - --spring.datasource.druid.master.url=jdbc:mysql://172.18.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8&allowMultiQueries=true

'@ -replace "`r?`n", "`n")



[System.IO.File]::WriteAllText($p, $t, (New-Object System.Text.UTF8Encoding($false)))

"backend heap64/meta112/direct-driver patched"

