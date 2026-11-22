#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 - <<'PY'
from pathlib import Path
root = Path('/mnt/d/work/IdeaProjects')
poms = [
    root/'car-monit-api-jdk21/pom.xml',
    root/'car-monit-api-jdk17/pom.xml',
    root/'car-monit-backend-jdk21/pom.xml',
    root/'car-monit-backend-jdk17/pom.xml',
]
needle = '                    <parameters>true</parameters>'
add = needle + '\n                    <!-- Mandrel25 的 javac 25 默认不再自动跑注解处理器，Lombok 必需 -->\n                    <proc>full</proc>'
for p in poms:
    t = p.read_text(encoding='utf-8')
    if '<proc>full</proc>' in t:
        print('SKIP', p)
    elif needle in t:
        p.write_text(t.replace(needle, add, 1), encoding='utf-8')
        print('PATCHED', p)
    else:
        print('FATAL needle missing', p)
PY
