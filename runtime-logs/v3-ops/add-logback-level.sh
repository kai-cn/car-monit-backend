#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 - <<'PY'
import json
from pathlib import Path
root=Path('/home/dev/IdeaProjects')
entries=[{'name':'ch.qos.logback.classic.Level','allDeclaredMethods':True,'allDeclaredConstructors':True,'allPublicFields':True}]
for repo in ('car-monit-backend-jdk25','car-monit-backend-jdk21','car-monit-backend-jdk17'):
    p=root/repo/'ruoyi-admin/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json'
    data=json.loads(p.read_text(encoding='utf-8')); existing={e['name'] for e in data}
    for e in entries:
        if e['name'] not in existing: data.append(e)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PATCHED',p)
PY
