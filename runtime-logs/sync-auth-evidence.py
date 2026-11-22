#!/usr/bin/env python3
"""
@description 将 WSL 管理员鉴权复测证据复制到 backend master runtime-logs 并生成摘要。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/sync-auth-evidence.py
@dependencies WSL ext4 中 /home/dev/local-auth-retest 证据。
"""
import json
import shutil
from pathlib import Path

src = Path(r'\\wsl$\openEuler-24.03-LTS-SP4\home\dev\local-auth-retest')
dst = Path(r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs\wsl-retest-auth')
dst.mkdir(parents=True, exist_ok=True)
for name in ['junit-contract.json', 'junit-load.json', 'contract.log', 'load.log', 'app.log']:
    p = src / name
    if p.exists():
        shutil.copy2(p, dst / name)
contract = json.loads((dst / 'junit-contract.json').read_text(encoding='utf-8'))
load = json.loads((dst / 'junit-load.json').read_text(encoding='utf-8'))
auth_fail = sum(1 for r in contract.get('endpoints', []) if '认证失败' in str(r.get('body', '')))
lines = [
    '# WSL 本机管理员鉴权复测证据',
    '',
    f"- endpoints: {contract.get('endpoint_count')}",
    f'- auth_fail: {auth_fail}',
    f"- load_total: {load.get('total_requests')}",
    f"- load_ok: {load.get('ok')}",
    f"- load_errors: {load.get('errors')}",
    f"- business_4xx: {load.get('business_4xx')}",
    f"- business_5xx: {load.get('business_5xx')}",
    f"- rps: {round(load.get('rps', 0), 2)}",
    '',
]
(dst / 'evidence.md').write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines))
