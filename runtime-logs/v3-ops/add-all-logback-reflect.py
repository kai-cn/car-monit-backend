#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Register every Logback class for reflection in backend native-image hints."""
import json
import zipfile
from pathlib import Path

ROOT = Path('/mnt/d/work/IdeaProjects')
JARS = [
    Path('/home/dev/.m2/repository/ch/qos/logback/logback-core/1.5.38/logback-core-1.5.38.jar'),
    Path('/home/dev/.m2/repository/ch/qos/logback/logback-classic/1.5.38/logback-classic-1.5.38.jar'),
]

names = set()
for jar in JARS:
    with zipfile.ZipFile(jar) as z:
        for n in z.namelist():
            if n.endswith('.class') and '$' not in n:
                names.add(n[:-6].replace('/', '.'))

for repo in ('car-monit-backend-jdk21', 'car-monit-backend-jdk17'):
    p = ROOT / repo / 'ruoyi-admin/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json'
    data = json.loads(p.read_text(encoding='utf-8'))
    existing = {e['name'] for e in data}
    for name in sorted(names):
        if name not in existing:
            data.append({'name': name, 'allDeclaredMethods': True, 'allDeclaredConstructors': True})
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{p}: total={len(data)} logback={len(names)}')
