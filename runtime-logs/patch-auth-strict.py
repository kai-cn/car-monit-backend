#!/usr/bin/env python3
"""
@description 给 JUnit 压测模板补 Header 支持，并给对拍脚本增加严格模式，确保多语言必须与 Java 返回一致才算通过。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/patch-auth-strict.py
@dependencies 只修改 backend master 的 runtime-logs 文本脚本。
"""
from pathlib import Path

BASE = Path(r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs')
gen = BASE / 'generate_junit_suite.py'
t = gen.read_text(encoding='utf-8')
old = '''    private static long percentile(List<Long> sorted, double p) {'''
new = '''    private static Map<String, String> headers() {
        Map<String, String> out = new LinkedHashMap<String, String>();
        String raw = env("ENDPOINT_HEADERS", "");
        for (String line : raw.split("\\\\r?\\\\n")) {
            int i = line.indexOf(':');
            if (i > 0) out.put(line.substring(0, i).trim(), line.substring(i + 1).trim());
        }
        return out;
    }

    private static long percentile(List<Long> sorted, double p) {'''
assert old in t and 'private static Map<String, String> headers()' not in t.split('LOAD = r\'\'\'')[1]
t = t.replace(old, new, 1)
old = '''                        c.setReadTimeout(Integer.parseInt(env("HTTP_TIMEOUT_MS", "60000")));
                        int status = c.getResponseCode();'''
new = '''                        c.setReadTimeout(Integer.parseInt(env("HTTP_TIMEOUT_MS", "60000")));
                        for (Map.Entry<String, String> h : headers().entrySet()) c.setRequestProperty(h.getKey(), h.getValue());
                        int status = c.getResponseCode();'''
assert old in t
t = t.replace(old, new, 1)
gen.write_text(t, encoding='utf-8')
print('PATCHED load headers')

pc = BASE / 'parity_compare.py'
t = pc.read_text(encoding='utf-8')
old = '''    ap.add_argument('--allow-diff-status', default='', help='comma-separated statuses that may differ')
'''
new = '''    ap.add_argument('--allow-diff-status', default='', help='comma-separated statuses that may differ')
    ap.add_argument('--strict', action='store_true', help='require every endpoint exact/semantic match; NONDET is not a pass')
'''
assert old in t
t = t.replace(old, new, 1)
old = '''    print('COMPARE label=%s endpoints=%d fails=%d' % (a.label, len(keys), fails))

    sys.exit(0 if fails == 0 else 1)'''
new = '''    strict_bad = 0
    if a.strict:
        for row in rows:
            if row.get('verdict') != 'OK':
                strict_bad += 1
    print('COMPARE label=%s endpoints=%d fails=%d strict_bad=%d' % (a.label, len(keys), fails, strict_bad))

    sys.exit(0 if fails == 0 and strict_bad == 0 else 1)'''
assert old in t
t = t.replace(old, new, 1)
pc.write_text(t, encoding='utf-8')
print('PATCHED strict parity')
