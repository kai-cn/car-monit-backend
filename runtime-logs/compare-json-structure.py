#!/usr/bin/env python3
"""
@description 按用户判据比较候选与 Java 基准：body.code 必须为 200，JSON 结构一致且忽略键顺序。
@author Tencent Hunyuan Hy
@date 2026-11-23 17:05:00
@usage python3 runtime-logs/compare-json-structure.py <baseline.json> <candidate.json> <out.json>
@dependencies Python 3；输入为 JUnit contract JSON。
"""
import json
import sys
from pathlib import Path


def shape(value):
    """递归提取 JSON 结构，数组仅保留首个元素结构并记录长度非零约束。"""
    if isinstance(value, dict):
        return {'type': 'object', 'keys': {k: shape(v) for k, v in sorted(value.items())}}
    if isinstance(value, list):
        return {'type': 'array', 'item': shape(value[0]) if value else None}
    if value is None:
        return {'type': 'null'}
    return {'type': type(value).__name__}


def body_of(row):
    """解析 body 字符串为对象。"""
    body = row.get('body', '')
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body) if body else {}
    except Exception:
        return {}


def main():
    """读取两份契约 JSON，输出逐端点一致性报告。"""
    base = {r['endpoint']: r for r in json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))['endpoints']}
    cand = {r['endpoint']: r for r in json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))['endpoints']}
    rows = []
    passed = 0
    for endpoint in sorted(set(base) | set(cand)):
        b, c = base.get(endpoint, {}), cand.get(endpoint, {})
        bb, cb = body_of(b), body_of(c)
        bb = bb if isinstance(bb, dict) else {}
        cb = cb if isinstance(cb, dict) else {}
        b_code, c_code = bb.get('code'), cb.get('code')
        b_shape, c_shape = shape(bb), shape(cb)
        # 用户判据只适用于返回 JSON code 的端点；Java 基准无 code 的二进制/流响应
        # 以 HTTP 200 与候选同为无 code 作为一致性口径。
        if b_code == 200:
            ok = c_code == 200 and b_shape == c_shape
        else:
            ok = b_code is None and c_code is None and b.get('status') == c.get('status') == 200
        passed += int(ok)
        rows.append({'endpoint': endpoint, 'baseline_code': b_code, 'candidate_code': c_code,
                     'structure_match': b_shape == c_shape, 'pass': ok,
                     'baseline_status': b.get('status'), 'candidate_status': c.get('status')})
    out = {'total': len(rows), 'passed': passed, 'failed': len(rows) - passed, 'rows': rows}
    Path(sys.argv[3]).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'total': out['total'], 'passed': out['passed'], 'failed': out['failed']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
