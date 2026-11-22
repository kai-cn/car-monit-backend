# @description 历史脚本 dispatch-dbupgrade.ps1：派发或重派云端 runner 任务；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage powershell -File dispatch-dbupgrade.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# 用途：以运行时生成的临时口令触发两仓库 db-upgrade-cloud 云验证（口令不入库、不回显）。

# 用法：powershell -File dispatch-dbupgrade.ps1

$ErrorActionPreference = 'Stop'

$py = 'python'

$helper = 'D:/work/IdeaProjects/car-monit-api-java-V3/scripts/v3/ops/v3-github-actions-dispatch.py'



# 生成满足 openGauss 复杂度要求的临时测试口令，仅存在于本进程环境。

$pw = (& $py -c "import secrets; print(secrets.token_urlsafe(14) + 'Aa1@')").Trim()

$env:CARMONIT_CI_DB_PASSWORD = $pw



& $py $helper dispatch --repo kai-cn/car-monit-api --workflow db-upgrade-cloud.yml --ref feature-dbupgrade --input db_scope=both --input "ci_db_password=$pw"

& $py $helper dispatch --repo kai-cn/car-monit-backend --workflow db-upgrade-cloud.yml --ref feature-dbupgrade --input "ci_db_password=$pw"



Remove-Item Env:CARMONIT_CI_DB_PASSWORD -ErrorAction SilentlyContinue

