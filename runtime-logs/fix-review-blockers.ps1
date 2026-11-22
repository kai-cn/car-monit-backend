# @description 历史脚本 fix-review-blockers.ps1：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage powershell -File fix-review-blockers.ps1 [params]；参数含义见脚本原有注释。
# @dependencies Docker CLI 与已启动的守护进程；Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
$ErrorActionPreference = 'Stop'

$branches = @(
    @{ dir = 'car-monit-api-jdk17'; jdk = '17' },
    @{ dir = 'car-monit-api-jdk21'; jdk = '21' },
    @{ dir = 'car-monit-api-jdk25'; jdk = '25' }
)

function Write-File([string]$path, [string]$text) {
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($path, $text, $enc)
}

foreach ($b in $branches) {
    $root = "d:\work\IdeaProjects\$($b.dir)"
    $jdk = $b.jdk

    # BLOCK-1 / BLOCK-2: align build+runtime JDK with branch, inject Orika add-opens
    $dockerfile = @"
# Java service image (Spring Boot 4.1.2 / JDK $jdk, bytecode --release $jdk)
# Build context = repo root:
#   docker build -f docker/java.Dockerfile -t car-monit-api .
# Boot 4.1.2 / Spring Framework 7 require JDK 17+; this branch builds and runs on JDK $jdk.
# Credentials/URLs are injected via Spring environment variables, never baked into the image.
# Orika 1.5.4 needs --add-opens=java.base/java.lang=ALL-UNNAMED on JDK 17+ (Object#clone reflection).
FROM maven:3.9.9-eclipse-temurin-$jdk AS build

WORKDIR /build

COPY pom.xml ./
COPY pro-base-common/pom.xml pro-base-common/
COPY pro-business-api/pom.xml pro-business-api/

COPY pro-base-common/src pro-base-common/src
COPY pro-business-api/src pro-business-api/src

RUN mvn -B -ntp -DskipTests package

FROM eclipse-temurin:$jdk-jre-jammy

RUN groupadd --system carmonit \
 && useradd --system --gid carmonit --no-create-home carmonit

WORKDIR /app
COPY --from=build /build/pro-business-api/target/pro-business-api-1.0.jar /app/app.jar

USER carmonit
EXPOSE 9902

ENV JAVA_OPTS="-Xms256m -Xmx512m"
ENTRYPOINT ["sh", "-c", "exec java `$JAVA_OPTS --add-opens=java.base/java.lang=ALL-UNNAMED -jar /app/app.jar"]
"@
    Write-File "$root\docker\java.Dockerfile" $dockerfile

    # BLOCK-2: standalone deployment JVM opts + Boot 3/4 env var prefixes
    $envExample = @"
# Java standalone deployment env template (placeholders only, no real credentials)
# --add-opens is REQUIRED by Orika 1.5.4 on JDK 17+ (see docs/v3/springboot4-migration.md).
JAVA_OPTS=-Xms256m -Xmx512m --add-opens=java.base/java.lang=ALL-UNNAMED
SPRING_PROFILES_ACTIVE=prod

# Database (GaussDB / PostgreSQL protocol)
SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL=jdbc:postgresql://<DB_HOST>:5432/<DB_NAME>
SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=<DB_USER>
SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD=<DB_PASSWORD>

# Redis (Boot 3/4 uses spring.data.redis.*)
SPRING_DATA_REDIS_HOST=<REDIS_HOST>
SPRING_DATA_REDIS_PORT=6379

# Elasticsearch (custom elasticsearch.host / elasticsearch.port)
ELASTICSEARCH_HOST=<ES_HOST>
ELASTICSEARCH_PORT=9200

# Kafka
SPRING_KAFKA_BOOTSTRAP_SERVERS=<KAFKA_HOST>:9092

# Internal endpoint token (must match backend TRAFFIC_API_INTERNAL_TOKEN)
TRAFFIC_INTERNAL_TOKEN=<INTERNAL_TOKEN>
"@
    Write-File "$root\deploy\standalone\config\java.env.example" $envExample

    $readme = [System.IO.File]::ReadAllText("$root\deploy\standalone\README.md")
    $readme = $readme.Replace(
        'JAVA_OPTS=-Xms256m -Xmx512m',
        'JAVA_OPTS=-Xms256m -Xmx512m --add-opens=java.base/java.lang=ALL-UNNAMED')
    if ($readme -notmatch 'Orika') {
        $note = "`r`n`r`n> --add-opens=java.base/java.lang=ALL-UNNAMED is REQUIRED by Orika 1.5.4 on JDK 17+;`r`n> removing it makes startup fail with InaccessibleObjectException. See docs/v3/springboot4-migration.md.`r`n"
        $readme = $readme.TrimEnd() + $note
    }
    Write-File "$root\deploy\standalone\README.md" $readme

    # systemd: hard-code add-opens as a fallback even if env.example is not copied verbatim
    $svc = [System.IO.File]::ReadAllText("$root\deploy\standalone\systemd\car-monit-api-java.service")
    $oldExec = "ExecStart=/bin/sh -c 'exec /usr/bin/java `$JAVA_OPTS -jar @PREFIX@/java/app.jar'"
    $newExec = "ExecStart=/bin/sh -c 'exec /usr/bin/java `$JAVA_OPTS --add-opens=java.base/java.lang=ALL-UNNAMED -jar @PREFIX@/java/app.jar'"
    $svc = $svc.Replace($oldExec, $newExec)
    Write-File "$root\deploy\standalone\systemd\car-monit-api-java.service" $svc
}

'patched 3 branches: Dockerfile / java.env.example / README.md / systemd unit'
