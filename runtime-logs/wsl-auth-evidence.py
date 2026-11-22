#!/usr/bin/env python3
"""
@description 汇总 WSL 管理员鉴权复测证据，统计认证失败与状态码分布。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/wsl-auth-evidence.py
@dependencies WSL 路径 /home/dev/local-auth-retest。
"""
import json
from collections import Counter
from pathlib import Path

root = Path('/home/dev/local-auth-retest')
contract = json.loads((root / 'junit-contract.json').read_text(encoding='utf-8'))
rows = contract.get('endpoints', [])
auth_fail = sum(1 for r in rows if '认证失败' in str(r.get('body', '')))
print('endpoints', len(rows))
print('auth_fail', auth_fail)
print('status_counts', Counter(int(r.get('status', 0)) for r in rows).most_common(8))
load = json.loads((root / 'junit-load.json').read_text(encoding='utf-8'))
print('load', load.get('total_requests'), load.get('ok'), load.get('errors'),
      load.get('business_4xx'), load.get('business_5xx'), round(load.get('rps', 0), 2))
