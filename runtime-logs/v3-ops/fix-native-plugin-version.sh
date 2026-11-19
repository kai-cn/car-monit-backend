#!/usr/bin/env bash
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
