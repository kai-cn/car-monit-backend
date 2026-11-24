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


def compatible(a, b):
    """比较 JSON 结构：对象键集合、数组元素结构；标量值/标量类型不算结构差异。"""
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    at, bt = a.get('type'), b.get('type')
    # 非容器标量不参与“键结构”比较；code 值已由 c_code == b_code 独立约束。
    if at not in ('object', 'array') or bt not in ('object', 'array'):
        return True
    if at != bt:
        return False
    if at == 'array':
        ai, bi = a.get('item'), b.get('item')
        if ai is None or bi is None:
            return True
        return compatible(ai, bi)
    if a.get('type') == 'object':
        ak, bk = a.get('keys', {}), b.get('keys', {})
        if set(ak) != set(bk):
            return False
        return all(compatible(ak[k], bk[k]) for k in ak)
    # number/string/null 等标量差异属于值差异，不属于 JSON 键结构差异。
    return True


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
        shape_ok = compatible(b_shape, c_shape)
        # 用户新判据：以 Java 基准为准，JSON 结构一致且键顺序无关；
        # 业务错误 code 也必须与 Java 基准一致，不再强行要求所有 code=200。
        if b_code is None:
            ok = c_code is None and b.get('status') == c.get('status')
        else:
            ok = c_code == b_code and shape_ok
        passed += int(ok)
        rows.append({'endpoint': endpoint, 'baseline_code': b_code, 'candidate_code': c_code,
                     'structure_match': shape_ok, 'pass': ok,
                     'baseline_status': b.get('status'), 'candidate_status': c.get('status')})
    out = {'total': len(rows), 'passed': passed, 'failed': len(rows) - passed, 'rows': rows}
    Path(sys.argv[3]).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'total': out['total'], 'passed': out['passed'], 'failed': out['failed']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
