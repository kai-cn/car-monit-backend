#!/usr/bin/env python3
"""Summarize non-200 endpoint categories.

@description 按错误文本归类 endpoint body.code 非 200 记录，定位共性根因。
@author Tencent Hunyuan Hy
@date 2026-11-23 00:50:46
@usage python runtime-logs/summarize-non200.py <analysis.json>
@dependencies Python 3 标准库。
"""
import json
import sys
from collections import Counter
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
rows = [x for x in data['endpoints'] if x['verdict'] == 'non_200']
c = Counter()
for x in rows:
    b = x['body_prefix']
    if 'geometry_copy1' in b:
        c['geometry_copy1'] += 1
    elif 'UNAVAILABLE' in b or 'CIRCUIT_OPEN' in b:
        c['data_service_unavailable'] += 1
    elif '9902' in b and 'Connection refused' in b:
        c['api_9902_refused'] += 1
    elif '认证失败' in b:
        c['auth'] += 1
    elif '"code":500' in b or '"code":503' in b:
        c['other_5xx'] += 1
    else:
        c['other'] += 1
print('CATEGORIES', dict(c))
for x in rows:
    print(x['endpoint'], x['code'], x['body_prefix'][:140])
