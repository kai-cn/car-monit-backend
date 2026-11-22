#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-junit-load-metrics.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Separate transport errors from business status codes in generated load test.

Idea:
- Full endpoint lists contain protected URLs and parameterized routes that may
  legitimately answer 4xx/5xx without auth or request body.
- Load gate should measure transport health (status 0/exception), while 4xx/5xx
  counts are recorded as business-response evidence.
- compare_load.py remains unchanged because it compares the emitted fields.
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\generate_junit_suite.py')
t = p.read_text(encoding='utf-8')
old = '''        final AtomicLong errors = new AtomicLong();
        final AtomicLong bytes = new AtomicLong();'''
new = '''        final AtomicLong errors = new AtomicLong();
        final AtomicLong business4xx = new AtomicLong();
        final AtomicLong business5xx = new AtomicLong();
        final AtomicLong bytes = new AtomicLong();'''
assert old in t
t = t.replace(old, new, 1)
old = '''                        total.incrementAndGet();
                        if (status < 500) ok.incrementAndGet(); else errors.incrementAndGet();'''
new = '''                        total.incrementAndGet();
                        if (status >= 500) business5xx.incrementAndGet();
                        else if (status >= 400) business4xx.incrementAndGet();
                        else ok.incrementAndGet();'''
assert old in t
t = t.replace(old, new, 1)
old = '''        result.put("errors", errors.get());
        result.put("rps", seconds == 0 ? 0 : (double) total.get() / seconds);'''
new = '''        result.put("errors", errors.get());
        result.put("business_4xx", business4xx.get());
        result.put("business_5xx", business5xx.get());
        result.put("rps", seconds == 0 ? 0 : (double) total.get() / seconds);'''
assert old in t
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('patched load metrics')
