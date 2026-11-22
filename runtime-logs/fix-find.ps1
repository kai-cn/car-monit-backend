# @description 历史脚本 fix-find.ps1：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage powershell -File fix-find.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

$branches = @('car-monit-api-jdk17', 'car-monit-api-jdk21', 'car-monit-api-jdk25')

foreach ($r in $branches) {

    $p = "d:\work\IdeaProjects\$r\.github\workflows\self-hosted-ci.yml"

    $t = [System.IO.File]::ReadAllText($p)

    $t = $t.Replace(

        'CLASS_FILE=$(find pro-business-api/target/classes -name "*.class" | head -1)',

        "CLASS_FILE=`$(find pro-business-api/target/classes -name '*.class' -print -quit)")

    [System.IO.File]::WriteAllText($p, $t, (New-Object System.Text.UTF8Encoding($false)))

}

'patched find -print -quit (avoid SIGPIPE under pipefail)'

