#!/usr/bin/env python3
"""
@description 删除压测模板中误重复插入的 headers 方法，恢复 Java8 编译通过。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/fix-duplicate-load-headers.py
@dependencies 只修改 backend master 的 generate_junit_suite.py。
"""
from pathlib import Path

p = Path(r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs\generate_junit_suite.py')
t = p.read_text(encoding='utf-8')
load_start = t.index("LOAD = r'''")
head, load = t[:load_start], t[load_start:]
block = '''    private static Map<String, String> headers() {
        Map<String, String> out = new LinkedHashMap<String, String>();
        String raw = env("ENDPOINT_HEADERS", "");
        for (String line : raw.split("\\\\r?\\\\n")) {
            int i = line.indexOf(':');
            if (i > 0) out.put(line.substring(0, i).trim(), line.substring(i + 1).trim());
        }
        return out;
    }
'''
# Keep exactly one headers method in the LOAD template.
first = load.find(block)
second = load.find(block, first + len(block)) if first >= 0 else -1
if second >= 0:
    load = load[:second] + load[second + len(block):]
    p.write_text(head + load, encoding='utf-8')
    print('REMOVED_DUPLICATE')
else:
    print('NO_DUPLICATE')
