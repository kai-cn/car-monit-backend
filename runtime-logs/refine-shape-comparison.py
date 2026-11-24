#!/usr/bin/env python3
"""
@description 细化 JSON 结构比较：数组元素结构以非空一侧为准，空数组作为结构通配。
@author Tencent Hunyuan Hy
@date 2026-11-24 21:10:00
@usage python3 runtime-logs/refine-shape-comparison.py
@dependencies Python 3；修改 runtime-logs/compare-json-structure.py。
"""
from pathlib import Path

p = Path('/home/dev/IdeaProjects/car-monit-backend/runtime-logs/compare-json-structure.py')
t = p.read_text(encoding='utf-8')
anchor = '''def body_of(row):'''
helper = '''def compatible(a, b):
    """比较两个 shape；空数组的 item=None 作为通配符。"""
    if not isinstance(a, dict) or not isinstance(b, dict):
        return a == b
    if a.get('type') != b.get('type'):
        return False
    if a.get('type') == 'array':
        ai, bi = a.get('item'), b.get('item')
        if ai is None or bi is None:
            return True
        return compatible(ai, bi)
    if a.get('type') == 'object':
        ak, bk = a.get('keys', {}), b.get('keys', {})
        if set(ak) != set(bk):
            return False
        return all(compatible(ak[k], bk[k]) for k in ak)
    return True


'''
assert anchor in t
t = t.replace(anchor, helper + anchor, 1)
t = t.replace("b_shape, c_shape = shape(bb), shape(cb)", "b_shape, c_shape = shape(bb), shape(cb)\n        shape_ok = compatible(b_shape, c_shape)")
t = t.replace("b_shape == c_shape", "shape_ok")
p.write_text(t, encoding='utf-8')
print('SHAPE_COMPARISON_REFINED')
