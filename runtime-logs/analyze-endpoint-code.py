#!/usr/bin/env python3
"""Analyze endpoint response bodies by the new code-based success criterion.

@description 按 body.code==200 判据分析 endpoint JSON，区分成功、待定和非 200。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:33:26
@usage python runtime-logs/analyze-endpoint-code.py <contract.json> [out.json]
@dependencies Python 3 标准库。
"""
import json
import sys
from collections import Counter
from pathlib import Path


def extract_body_code(row: dict):
    """从 endpoint 记录中提取 body.code；body 缺失或 JSON 解析失败返回待定。"""
    body = row.get('body', '')
    if isinstance(body, dict):
        obj = body
    else:
        try:
            obj = json.loads(str(body))
        except Exception:
            return None, 'no_code'
    if isinstance(obj, dict) and 'code' in obj:
        return obj.get('code'), 'code'
    return None, 'no_code'


def main() -> None:
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name('endpoint-code-analysis.json')
    data = json.loads(src.read_text(encoding='utf-8'))
    rows = data.get('endpoints', [])
    results = []
    counts = Counter()
    for row in rows:
        code, kind = extract_body_code(row)
        if kind == 'code' and code == 200:
            verdict = 'success'
        elif kind == 'code':
            verdict = 'non_200'
        else:
            verdict = 'pending_no_code'
        counts[verdict] += 1
        results.append({'endpoint': row.get('endpoint'), 'status': row.get('status'), 'code': code, 'verdict': verdict,
                        'body_prefix': str(row.get('body', ''))[:240]})
    report = {'source': str(src), 'total': len(rows), 'counts': dict(counts), 'endpoints': results}
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report['counts'], ensure_ascii=False))
    print('WROTE', out)


if __name__ == '__main__':
    main()
