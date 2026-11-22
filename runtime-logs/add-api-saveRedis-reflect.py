#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
import json
from pathlib import Path
p = Path(r'D:\work\runtime-logs\api25-reflect.json')
data = json.loads(p.read_text(encoding='utf-8'))
entry = {
    'name': 'com.ruoyi.base.domain.SysUtil',
    'allDeclaredConstructors': True,
    'allDeclaredMethods': True,
    'allDeclaredFields': True,
}
if not any(e.get('name') == entry['name'] for e in data):
    data.append(entry)
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('entries', len(data))
