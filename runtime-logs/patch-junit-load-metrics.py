#!/usr/bin/env python3

"""
@description 历史脚本 patch-junit-load-metrics.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python patch-junit-load-metrics.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

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

