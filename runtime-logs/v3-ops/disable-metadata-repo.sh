#!/usr/bin/env bash

# @description 历史脚本 disable-metadata-repo.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash disable-metadata-repo.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

python3 - <<'PY'

from pathlib import Path

root = Path('/home/dev/IdeaProjects')

targets = [

    root/'car-monit-api-jdk21/pro-business-api/pom.xml',

    root/'car-monit-api-jdk17/pro-business-api/pom.xml',

    root/'car-monit-backend-jdk21/ruoyi-admin/pom.xml',

    root/'car-monit-backend-jdk17/ruoyi-admin/pom.xml',

]

needle = '                <configuration>\n                    <!-- grpc-netty-shaded'

add = ('                <configuration>\n'

       '                    <version>1.1.14</version>\n'

       '                    <metadataRepository><enabled>false</enabled></metadataRepository>\n'

       '                    <!-- grpc-netty-shaded')

for p in targets:

    t = p.read_text(encoding='utf-8')

    if '<metadataRepository>' in t:

        print('SKIP', p)

    elif needle in t:

        p.write_text(t.replace(needle, add, 1), encoding='utf-8')

        print('PATCHED', p)

    else:

        # backend 的注释不同：直接用 configuration 后第一行

        n2 = '                <configuration>\n'

        pos = t.find(n2, t.find('native-maven-plugin'))

        if pos < 0:

            print('FATAL', p)

        else:

            pos += len(n2)

            p.write_text(t[:pos] + '                    <version>1.1.14</version>\n                    <metadataRepository><enabled>false</enabled></metadataRepository>\n' + t[pos:], encoding='utf-8')

            print('PATCHED(fallback)', p)

PY

