# @description 历史脚本 start-api-jdk17-sb4.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage powershell -File start-api-jdk17-sb4.ps1 [params]；参数含义见脚本原有注释。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# 启动 car-monit-api (Spring Boot 4.1.2 / JDK 17) 的本地联调脚本

# 凭据不落盘：DB 口令与内部令牌一律由运行环境注入（未注入则直接失败）。

$ErrorActionPreference = 'Stop'



$env:JAVA_HOME = 'D:\jdk\temurin-17\jdk-17.0.21+9'

$java = Join-Path $env:JAVA_HOME 'bin\java.exe'

$jar  = 'D:\work\IdeaProjects\car-monit-api-jdk17\pro-business-api\target\pro-business-api-1.0.jar'

$logDir = 'D:\work\runtime-logs'

$logFile = Join-Path $logDir 'api-jdk17-sb4.log'



if (-not (Test-Path $jar)) { throw "jar not found: $jar" }



$busy = Get-NetTCPConnection -State Listen -LocalPort 9902 -ErrorAction SilentlyContinue

if ($busy) { throw "port 9902 already in use by PID $($busy.OwningProcess); stop it first" }



if (-not $env:SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD) {

    throw 'SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD is required (inject via environment)'

}



# openGauss 现在跑在 WSL docker，Windows 侧经 localhost 转发访问；库名/用户沿用原配置

$dsUrl = 'jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&tinyInt1isBit=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai'



$argList = @(

  '-Xms512m', '-Xmx1024m',

  '-XX:+UseG1GC',

  '-Dfile.encoding=UTF-8',

  '-Duser.timezone=Asia/Shanghai',

  # Orika 1.5.4 + 新版 javassist 在 JDK 17 下需要反射 java.lang.Object#clone

  '--add-opens=java.base/java.lang=ALL-UNNAMED',

  '-jar', $jar,

  '--server.port=9902',

  "--spring.datasource.dynamic.datasource.master.url=$dsUrl"

)



Start-Process -FilePath $java -ArgumentList $argList -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err" -NoNewWindow -PassThru |

  Select-Object Id,ProcessName

Write-Host "api starting, log: $logFile"

