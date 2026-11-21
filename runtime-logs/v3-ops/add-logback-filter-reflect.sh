#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 - <<'PY'
import json, zipfile
from pathlib import Path
root=Path('/home/dev/IdeaProjects')
jars=[Path('/home/dev/.m2/repository/ch/qos/logback/logback-core/1.5.38/logback-core-1.5.38.jar'),
      Path('/home/dev/.m2/repository/ch/qos/logback/logback-classic/1.5.38/logback-classic-1.5.38.jar')]
names=set()
for jar in jars:
    with zipfile.ZipFile(jar) as z:
        for n in z.namelist():
            if n.endswith('.class') and '$' not in n:
                c=n[:-6].replace('/','.')
                if c.startswith('ch.qos.logback.classic.filter.') or c.startswith('ch.qos.logback.core.filter.'):
                    names.add(c)
for repo in ('car-monit-backend-jdk25','car-monit-backend-jdk21','car-monit-backend-jdk17'):
    p=root/repo/'ruoyi-admin/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json'
    data=json.loads(p.read_text(encoding='utf-8')); existing={e['name'] for e in data}
    for name in sorted(names):
        if name not in existing:
            data.append({'name':name,'allDeclaredMethods':True,'allDeclaredConstructors':True})
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PATCHED',p,'added',len(names))
PY
