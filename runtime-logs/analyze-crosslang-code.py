#!/usr/bin/env python3
"""Analyze cross-language contract JSON files by body.code.

@description 按 body.code==200 判据统计后端、各语言候选的 endpoint 成功/待定/非 200，并检查是否保存了具体 JSON body。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:33:26
@usage python runtime-logs/analyze-crosslang-code.py [evidence_root] [out.json]
@dependencies Python 3 标准库；读取 crosslang-evidence 目录中的 junit-contract.json。
"""
import json
import sys
from collections import Counter
from pathlib import Path


def code_of(row):
    """返回 (code, verdict)。无 code 字段记 pending。"""
    body = row.get('body', '')
    if isinstance(body, dict):
        obj = body
    else:
        try:
            obj = json.loads(str(body))
        except Exception:
            return None, 'pending_no_code'
    if isinstance(obj, dict) and 'code' in obj:
        code = obj.get('code')
        return code, 'success' if code == 200 else 'non_200'
    return None, 'pending_no_code'


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r'D:\work\runtime-logs\crosslang-evidence')
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else root.parent / 'crosslang-code-analysis.json'
    summary = []
    for contract in sorted(root.rglob('junit-contract.json')):
        rel = contract.relative_to(root).as_posix()
        try:
            data = json.loads(contract.read_text(encoding='utf-8'))
        except Exception as e:
            summary.append({'source': rel, 'error': str(e)})
            continue
        rows = data.get('endpoints', [])
        counts = Counter()
        examples = []
        body_recorded = 0
        for row in rows:
            if 'body' in row and str(row.get('body', '')).strip():
                body_recorded += 1
            code, verdict = code_of(row)
            counts[verdict] += 1
            if verdict == 'non_200' and len(examples) < 5:
                examples.append({'endpoint': row.get('endpoint'), 'status': row.get('status'), 'code': code,
                                 'body_prefix': str(row.get('body', ''))[:200]})
        summary.append({'source': rel, 'total': len(rows), 'body_recorded': body_recorded,
                        'counts': dict(counts), 'non_200_examples': examples})
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    for item in summary:
        if 'counts' in item:
            print(item['source'], item['total'], item['body_recorded'], item['counts'])
        else:
            print(item['source'], item['error'])
    print('WROTE', out)


if __name__ == '__main__':
    main()
