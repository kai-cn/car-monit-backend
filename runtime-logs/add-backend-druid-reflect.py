#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
import json
from pathlib import Path
p = Path(r'D:\work\runtime-logs\bk25-reflect.json')
data = json.loads(p.read_text(encoding='utf-8'))
names = [
    'com.ruoyi.framework.config.properties.DruidProperties',
    'com.ruoyi.framework.config.DruidConfig',
    'com.ruoyi.framework.datasource.DynamicDataSource',
    'com.alibaba.druid.pool.DruidDataSource',
    'com.alibaba.druid.spring.boot4.autoconfigure.DruidDataSourceBuilder',
]
existing = {e.get('name') for e in data}
for n in names:
    if n not in existing:
        data.append({'name': n, 'allDeclaredConstructors': True,
                     'allDeclaredMethods': True, 'allDeclaredFields': True})
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('entries', len(data))
