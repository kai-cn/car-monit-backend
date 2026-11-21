#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
import json
from pathlib import Path

# backend: MyBatis Configuration reflection
p = Path(r'D:\work\runtime-logs\bk25-reflect.json')
data = json.loads(p.read_text(encoding='utf-8'))
entry = {'name': 'com.baomidou.mybatisplus.core.MybatisConfiguration',
         'allDeclaredConstructors': True, 'allDeclaredMethods': True}
if not any(e.get('name') == entry['name'] for e in data):
    data.append(entry)
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('backend reflect entries', len(data))

# boot3: include MySQL error resource bundle
p = Path(r'D:\work\runtime-logs\api-boot3-module-pom.xml')
t = p.read_text(encoding='utf-8')
needle = '                        <buildArg>--no-fallback</buildArg>'
add = needle + '\n                        <buildArg>-H:IncludeResources=com/mysql/cj/LocalizedErrorMessages.*</buildArg>'
if 'LocalizedErrorMessages' not in t:
    t = t.replace(needle, add, 1)
p.write_text(t, encoding='utf-8')
print('boot3 resource included', 'LocalizedErrorMessages' in t)
