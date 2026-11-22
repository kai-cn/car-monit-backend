#!/usr/bin/env bash

# @description 历史脚本 fix-native-plugin-version.sh：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash fix-native-plugin-version.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.

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

for p in targets:

    t = p.read_text(encoding='utf-8')

    t = t.replace('                    <version>1.1.14</version>\n                    <metadataRepository><enabled>false</enabled></metadataRepository>\n', '')

    needle = '                <artifactId>native-maven-plugin</artifactId>\n'

    if '<artifactId>native-maven-plugin</artifactId>\n                <version>1.1.14</version>' not in t:

        t = t.replace(needle, needle + '                <version>1.1.14</version>\n', 1)

    p.write_text(t, encoding='utf-8')

    print('FIXED', p)

PY

