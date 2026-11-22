#!/usr/bin/env bash

# @description 历史脚本 add-backend-mainclass.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash add-backend-mainclass.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

python3 - <<'PY'

from pathlib import Path

root = Path('/mnt/d/work/IdeaProjects')

needle = '                <artifactId>native-maven-plugin</artifactId>\n                <configuration>'

repl = ('                <artifactId>native-maven-plugin</artifactId>\n'

        '                <configuration>\n'

        '                    <mainClass>com.ruoyi.RuoYiApplication</mainClass>')

for repo in ('car-monit-backend-jdk21', 'car-monit-backend-jdk17'):

    p = root / repo / 'ruoyi-admin/pom.xml'

    t = p.read_text(encoding='utf-8')

    pos = t.find(needle)

    if pos < 0:

        print('FATAL needle missing', p)

        continue

    block_end = t.find('</configuration>', pos)

    block = t[pos:block_end]

    if '<mainClass>' in block:

        print('SKIP already in native plugin', p)

        continue

    p.write_text(t[:pos] + repl + t[pos + len(needle):], encoding='utf-8')

    print('PATCHED', p)

PY

