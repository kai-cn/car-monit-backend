# @description 历史脚本 harden.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage powershell -File harden.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Apply workflow security hardening rules across branches.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

$branches = @('car-monit-api-jdk17', 'car-monit-api-jdk21', 'car-monit-api-jdk25')

foreach ($r in $branches) {

    $root = "d:\work\IdeaProjects\$r"



    $p = "$root\.github\workflows\self-hosted-ci.yml"

    $t = [System.IO.File]::ReadAllText($p)

    $t = $t.Replace("grep -q -- '--add-opens=java.base/java.lang=ALL-UNNAMED'", "grep -Fq -- '--add-opens=java.base/java.lang=ALL-UNNAMED'")

    $t = $t.Replace(

        '          EXPECTED=$((44 + SPEC))',

        (@(

            '          test -n "$SPEC" || { echo "::error::cannot read java.specification.version"; exit 1; }',

            '          test -n "$CLASS_FILE" || { echo "::error::no compiled class found"; exit 1; }',

            '          test -n "$MAJOR" || { echo "::error::cannot read class major version"; exit 1; }',

            '          EXPECTED=$((44 + SPEC))'

        ) -join "`r`n"))

    [System.IO.File]::WriteAllText($p, $t, (New-Object System.Text.UTF8Encoding($false)))



    $w = "$root\pro-base-common\src\main\java\com\ruoyi\common\config\writer\RetRedisCacheWriter.java"

    $wt = [System.IO.File]::ReadAllText($w).Replace('deleted.intValue()', 'deleted.longValue()')

    [System.IO.File]::WriteAllText($w, $wt, (New-Object System.Text.UTF8Encoding($false)))



    $y = "$root\pro-business-api\src\main\resources\application.yml"

    $yt = [System.IO.File]::ReadAllText($y).Replace(

        '          username: gaussdb',

        '          username: ${SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME:gaussdb}')

    [System.IO.File]::WriteAllText($y, $yt, (New-Object System.Text.UTF8Encoding($false)))

}

'hardened: grep -Fq, smoke guards, longValue, username placeholder'

