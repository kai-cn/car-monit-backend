#!/usr/bin/env python3
"""
@description 历史脚本 patch-load-error-accounting.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python patch-load-error-accounting.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:

- count transport errors only when no HTTP status was obtained

- keep 4xx/5xx as business response buckets

- record up to three error samples for diagnosis without failing the suite
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\generate_junit_suite.py')
t = p.read_text(encoding='utf-8')
old = '''        final ConcurrentLinkedQueue<Long> latency = new ConcurrentLinkedQueue<Long>();
        final AtomicLong total = new AtomicLong();'''
new = '''        final ConcurrentLinkedQueue<Long> latency = new ConcurrentLinkedQueue<Long>();
        final ConcurrentLinkedQueue<String> errorSamples = new ConcurrentLinkedQueue<String>();
        final AtomicLong total = new AtomicLong();'''
assert old in t
t = t.replace(old, new, 1)
old = '''                    HttpURLConnection c = null;
                    long t0 = System.currentTimeMillis();
                    try {
                        c = (HttpURLConnection) new URL(base + path).openConnection();'''
new = '''                    HttpURLConnection c = null;
                    int statusSeen = 0;
                    long t0 = System.currentTimeMillis();
                    try {
                        c = (HttpURLConnection) new URL(base + path).openConnection();'''
assert old in t
t = t.replace(old, new, 1)
old = '''                        int status = c.getResponseCode();
                        InputStream in = status < 400 ? c.getInputStream() : c.getErrorStream();'''
new = '''                        int status = c.getResponseCode();
                        statusSeen = status;
                        InputStream in = status < 400 ? c.getInputStream() : c.getErrorStream();'''
assert old in t
t = t.replace(old, new, 1)
old = '''                    } catch (Exception e) {
                        total.incrementAndGet();
                        errors.incrementAndGet();
                    } finally {'''
new = '''                    } catch (Exception e) {
                        total.incrementAndGet();
                        if (statusSeen == 0) {
                            errors.incrementAndGet();
                        } else if (statusSeen >= 500) {
                            business5xx.incrementAndGet();
                        } else if (statusSeen >= 400) {
                            business4xx.incrementAndGet();
                        } else {
                            ok.incrementAndGet();
                        }
                        if (errorSamples.size() < 3) {
                            errorSamples.add(path + ": " + e.getClass().getSimpleName() + ": " + e.getMessage());
                        }
                    } finally {'''
assert old in t
t = t.replace(old, new, 1)
old = '''        result.put("bytes", bytes.get());
'''
new = '''        result.put("bytes", bytes.get());
        result.put("error_samples", new ArrayList<String>(errorSamples));
'''
assert old in t
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('patched load accounting')
