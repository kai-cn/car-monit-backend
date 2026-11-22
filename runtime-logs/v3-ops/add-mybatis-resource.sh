#!/usr/bin/env bash

# @description 历史脚本 add-mybatis-resource.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash add-mybatis-resource.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

python3 - <<'PY'

from pathlib import Path

for root in (Path('/home/dev/IdeaProjects'), Path('/mnt/d/work/IdeaProjects')):

    for repo in ('car-monit-backend-jdk25','car-monit-backend-jdk21','car-monit-backend-jdk17'):

        p=root/repo/'ruoyi-admin/pom.xml'

        t=p.read_text(encoding='utf-8')

        if 'mybatis/mybatis-config.xml' in t:

            print('SKIP',p); continue

        needle='                    <buildArgs>\n'

        add=needle+'                        <buildArg>-H:IncludeResources=mybatis/mybatis-config.xml</buildArg>\n'

        if needle in t:

            p.write_text(t.replace(needle,add,1),encoding='utf-8')

            print('PATCHED',p)

        else:

            print('NOT_FOUND',p)

PY

