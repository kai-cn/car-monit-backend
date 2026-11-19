#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Extract full GET endpoint list by importing the generated route registry."""
import re, json, sys, importlib.util

mod_path = r'D:\work\IdeaProjects\car-monit-api-java-V3\car-monit-api-python\app\routes\generated.py'
spec = importlib.util.spec_from_file_location('genroutes', mod_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
routes = mod.ROUTES
gets = [r for r in routes if r.get('http') == 'GET']
print('total routes:', len(routes), '| GET:', len(gets))


def to_probe(p):
    return re.sub(r'\{[^}]+\}', '1', p)


out = []
for r in gets:
    out.append({'path': r['path'], 'probe': to_probe(r['path']), 'method': r.get('method'),
                'returns': r.get('returns'),
                'controller': (r.get('controller') or '').split('.')[-1]})

with open(r'D:\work\runtime-logs\api-endpoints.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
with open(r'D:\work\runtime-logs\api-endpoints.txt', 'w', encoding='utf-8') as f:
    for e in out:
        f.write(e['probe'] + '\n')
print('written api-endpoints.json / .txt')
for e in out[:12]:
    print(' ', e['probe'], '->', (e['returns'] or '')[:32])
