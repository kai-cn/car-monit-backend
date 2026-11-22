# @description 历史脚本 patch-manifests.ps1：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage powershell -File patch-manifests.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

$p = 'D:\work\runtime-logs\manifests.yaml'

$t = [System.IO.File]::ReadAllText($p)



$apiOld = @'

          args:

            - --add-opens=java.base/java.lang=ALL-UNNAMED

            - -Xms48m

            - -Xmx112m

            - -XX:MaxMetaspaceSize=72m

            - -XX:ReservedCodeCacheSize=24m

            - -XX:MaxDirectMemorySize=16m

            - -Xss256k

            - -XX:CICompilerCount=2

            - -XX:+UseSerialGC

            - -Dfile.encoding=UTF-8

            - -Duser.timezone=Asia/Shanghai

            - -jar

            - /app/app.jar

            - --server.port=9902

            - --spring.datasource.dynamic.datasource.master.url=jdbc:postgresql://172.18.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&tinyInt1isBit=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai

            - --traffic.query.engine=legacy

            - --traffic.sync.enabled=false

'@ -replace "`r?`n", "`n"



$apiNew = @'

          args:

            - --add-opens=java.base/java.lang=ALL-UNNAMED

            - -Xms20m

            - -Xmx56m

            - -XX:MaxMetaspaceSize=120m

            - -XX:CompressedClassSpaceSize=12m

            - -XX:ReservedCodeCacheSize=4m

            - -XX:MaxDirectMemorySize=2m

            - -XX:MaxHeapFreeRatio=10

            - -XX:MinHeapFreeRatio=5

            - -Xss256k

            - -XX:CICompilerCount=2

            - -XX:+UseSerialGC

            - -XX:-UsePerfData

            - -Dsun.zip.disableMemoryMapping=true

            - -Djdk.nio.maxCachedBufferSize=65536

            - -Djava.util.concurrent.ForkJoinPool.common.parallelism=1

            - -Dfile.encoding=UTF-8

            - -Duser.timezone=Asia/Shanghai

            - -jar

            - /app/app.jar

            - --server.port=9902

            - --spring.datasource.dynamic.datasource.master.url=jdbc:postgresql://172.18.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&tinyInt1isBit=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai

            - --traffic.query.engine=legacy

            - --traffic.sync.enabled=false

            - --spring.main.lazy-initialization=true

            - --server.tomcat.threads.max=2

            - --server.tomcat.threads.min-spare=1

            - --spring.task.scheduling.pool.size=1

            - --spring.datasource.dynamic.druid.initial-size=1

            - --spring.datasource.dynamic.druid.min-idle=1

            - --spring.datasource.dynamic.druid.max-active=2

            - --logging.level.root=WARN

            - --logging.level.p6spy=OFF

            - --logging.level.com.baomidou=WARN

'@ -replace "`r?`n", "`n"



$backendOld = @'

          args:

            - -Xms48m

            - -Xmx112m

            - -XX:MaxMetaspaceSize=72m

            - -XX:ReservedCodeCacheSize=24m

            - -XX:MaxDirectMemorySize=16m

            - -Xss256k

            - -XX:CICompilerCount=2

            - -XX:+UseSerialGC

            - -Dfile.encoding=UTF-8

            - -Duser.timezone=Asia/Shanghai

            - -jar

            - /app/app.jar

            - --server.port=9989

            - --spring.datasource.druid.master.url=jdbc:p6spy:mysql://172.18.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8&allowMultiQueries=true

'@ -replace "`r?`n", "`n"



$backendNew = @'

          args:

            - -Xms20m

            - -Xmx56m

            - -XX:MaxMetaspaceSize=120m

            - -XX:CompressedClassSpaceSize=12m

            - -XX:ReservedCodeCacheSize=4m

            - -XX:MaxDirectMemorySize=2m

            - -XX:MaxHeapFreeRatio=10

            - -XX:MinHeapFreeRatio=5

            - -Xss256k

            - -XX:CICompilerCount=2

            - -XX:+UseSerialGC

            - -XX:-UsePerfData

            - -Dsun.zip.disableMemoryMapping=true

            - -Djdk.nio.maxCachedBufferSize=65536

            - -Djava.util.concurrent.ForkJoinPool.common.parallelism=1

            - -Dfile.encoding=UTF-8

            - -Duser.timezone=Asia/Shanghai

            - -jar

            - /app/app.jar

            - --server.port=9989

            - --spring.datasource.druid.master.url=jdbc:p6spy:mysql://172.18.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8&allowMultiQueries=true

            - --spring.main.lazy-initialization=true

            - --server.tomcat.threads.max=2

            - --server.tomcat.threads.min-spare=1

            - --spring.task.scheduling.pool.size=1

            - --spring.datasource.druid.initial-size=1

            - --spring.datasource.druid.min-idle=1

            - --spring.datasource.druid.max-active=2

            - --logging.level.root=WARN

            - --logging.level.p6spy=OFF

            - --logging.level.com.baomidou=WARN

'@ -replace "`r?`n", "`n"



$norm = $t -replace "`r`n", "`n"

$norm = $norm.Replace($apiOld, $apiNew)

$norm = $norm.Replace($backendOld, $backendNew)

[System.IO.File]::WriteAllText($p, $norm, (New-Object System.Text.UTF8Encoding($false)))

"patched: api=$($norm.Contains('-Xmx56m')) backend=$($norm.Contains('--server.port=9989'))"

