#!/usr/bin/env python3
"""
@description 修复 JUnit 证据 JSON 中未转义控制字符导致解析失败的问题。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/patch-json-control-chars.py
@dependencies 只修改 backend master 的 generate_junit_suite.py。
"""
from pathlib import Path

p = Path(r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs\generate_junit_suite.py')
t = p.read_text(encoding='utf-8')
old = '''            else if (c == '\\t') b.append("\\\\t");
            else b.append(c);'''
new = '''            else if (c == '\\t') b.append("\\\\t");
            else if (c < 0x20) b.append(String.format("\\\\u%04x", (int) c));
            else b.append(c);'''
assert old in t
p.write_text(t.replace(old, new, 1), encoding='utf-8')
print('PATCHED_JSON_CONTROL_CHARS')
