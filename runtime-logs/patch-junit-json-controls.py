#!/usr/bin/env python3
"""
@description 修复 JUnit 报告生成器对二进制响应体中控制字符的 JSON 转义。
@author Tencent Hunyuan Hy
@date 2026-11-23 09:01:14
@usage python3 runtime-logs/patch-junit-json-controls.py
@dependencies Python 3；仅修改 runtime-logs/generate_junit_suite.py 中的 Java 模板字符串。
"""
from pathlib import Path

p = Path('/mnt/d/work/runtime-logs/generate_junit_suite.py')
t = p.read_text(encoding='utf-8')
old = '''            else if (c == '\\t') b.append("\\\\t");
            else b.append(c);'''
new = '''            else if (c == '\\t') b.append("\\\\t");
            else if (c < 0x20) b.append(String.format("\\\\u%04x", (int) c));
            else b.append(c);'''
count = t.count(old)
assert count == 2, count
t = t.replace(old, new)
p.write_text(t, encoding='utf-8')
print('PATCHED_JSON_ESCAPE', count)
