#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 - <<'PY'
from pathlib import Path
for root in (Path('/home/dev/IdeaProjects'), Path('/mnt/d/work/IdeaProjects')):
    for repo in ('car-monit-backend-jdk25','car-monit-backend-jdk21','car-monit-backend-jdk17'):
        p = root/repo/'ruoyi-admin/pom.xml'
        t = p.read_text(encoding='utf-8')
        old = '            <artifactId>spring-boot-devtools</artifactId>\n            <optional>true</optional>'
        new = '            <artifactId>spring-boot-devtools</artifactId>\n            <scope>provided</scope>'
        if old in t:
            p.write_text(t.replace(old,new,1),encoding='utf-8')
            print('PATCHED',p)
        elif '<scope>provided</scope>' in t:
            print('SKIP',p)
        else:
            print('NOT_FOUND',p)
PY
