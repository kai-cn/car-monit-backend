#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
import json
from pathlib import Path

# Boot3 api: create hints from jdk25 file + RedisProperties classes
p = Path(r'D:\work\runtime-logs\api25-reflect.json')
data = json.loads(p.read_text(encoding='utf-8'))
names = [
    'org.springframework.boot.autoconfigure.data.redis.RedisProperties',
    'org.springframework.boot.autoconfigure.data.redis.RedisProperties$Pool',
    'org.springframework.boot.autoconfigure.data.redis.RedisProperties$Cluster',
    'org.springframework.boot.autoconfigure.data.redis.RedisProperties$Sentinel',
]
existing = {e.get('name') for e in data}
for n in names:
    if n not in existing:
        data.append({'name': n, 'allDeclaredConstructors': True,
                     'allDeclaredMethods': True, 'allDeclaredFields': True})
out = Path(r'D:\work\runtime-logs\boot3-reflect.json')
out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('boot3 reflect', len(data))

# backend: MyBatis Configuration reflection
p = Path(r'D:\work\runtime-logs\bk25-reflect.json')
data = json.loads(p.read_text(encoding='utf-8'))
for n in ['org.apache.ibatis.session.Configuration', 'org.apache.ibatis.builder.xml.XMLConfigBuilder']:
    if not any(e.get('name') == n for e in data):
        data.append({'name': n, 'allDeclaredConstructors': True,
                     'allDeclaredMethods': True, 'allDeclaredFields': True})
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('backend reflect', len(data))
